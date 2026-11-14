"""Catalog-first extension of the v3 Firecrawl engine; public retrieval, private gates.
A catalog is a lead source, never evidence of year, region, format or novelty.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import argparse, json
from pathlib import Path
from .firecrawl_research import build_index, load_history_archive, rest_transport, digest
from urllib.parse import urlsplit, urlunsplit
from .firecrawl_research import (CATALOG_SCHEMA, CATALOG_PROMPT, catalog_titles,
    title_key, names, run_round, public_evidence, FirecrawlProvider)


def canonical_url(url):
    if not isinstance(url, str): return ''
    p = urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname: return ''
    # Keep query parameters: some distributors use them as production IDs.
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/') or '/', p.query, ''))


def valid_source(receipt):
    return (isinstance(receipt,dict) and canonical_url(receipt.get('url')) and
            receipt.get('reviewed') is True and bool(receipt.get('excerpt')))

@dataclass
class Crosswalk:
    """Only reviewed, sourced identity relations. No title translations by inference."""
    rows: list = field(default_factory=list)
    def add(self, row):
        if not row.get('production_id') or not title_key(row.get('title')): raise ValueError('Missing identity')
        if not valid_source(row.get('source')): raise ValueError('Reviewed source and excerpt required')
        if row.get('relation','same') not in ('same','sequel','remake','edit'): raise ValueError('Unknown relation')
        if row.get('relation') in ('sequel','remake','edit') and not title_key(row.get('parent_title')): raise ValueError('Missing parent')
        self.rows.append(dict(row))
    def matching(self,candidate):
        keys={title_key(candidate.get('title'))}-{''}
        return [r for r in self.rows if keys & ({title_key(r['title']),*map(title_key,names(r.get('aliases')))}-{''})]
    def resolve(self,candidate):
        matches=self.matching(candidate)
        if len({r['production_id'] for r in matches})!=1: return dict(candidate)
        row=matches[0]
        # Do not add the parent title as an alias of a sequel/remake.
        return {**candidate,'aliases':list(dict.fromkeys([*names(candidate.get('aliases')),row['title'],*names(row.get('aliases'))])),
                **{k:row[k] for k in ('country','year','format') if k in row},
                'production_id':row['production_id'],'identity_review_sources':[r['source']['url'] for r in matches],
                'identity_verified_new':row.get('reviewed_novel') is True,
                'relation':row.get('relation','same'),'parent_title':row.get('parent_title')}

class CatalogIndex:
    """Wrap existing private index; allow a reviewed distinct sequel past parent-only fuzzy collision.
    Exact matches, history-only exact matches and unresolved competing aliases remain blocked.
    """
    def __init__(self,index,crosswalk): self.index=index; self.crosswalk=crosswalk
    def __getattr__(self,name): return getattr(self.index,name)
    def check(self,candidate):
        original=self.index.check(candidate)
        if original['state']=='known': return original
        c=self.crosswalk.resolve(candidate)
        # Check every verified alias, including newly resolved native names.
        result=self.index.check(c)
        if result['state']=='known': return result
        rows=self.crosswalk.matching(candidate)
        if len({r['production_id'] for r in rows})>1:
            return {'state':'quarantine','reason':'crosswalk_collision'}
        if c.get('relation')=='edit':
            return {'state':'known','reason':'alternate_edit_not_new','effective':{}}
        if result['state']=='quarantine' and result.get('reason')=='fuzzy_identity_review' and c.get('relation') in ('sequel','remake') and c.get('identity_verified_new'):
            parent=title_key(c.get('parent_title'))
            parent_records=self.index.by_key.get(parent,[])
            parent_keys={parent}
            for record in parent_records:
                parent_keys.update(title_key(n) for n in [record['title'],*record.get('aliases',[])])
            if parent_records and set(result.get('matches',[])) <= parent_keys:
                return {'state':'unresolved','reason':'verified_distinct_production_parent_only'}
        return result


def catalog_batches(provider, plan, ledger):
    """Run bounded catalog operations in plan order. Record errors; never imply exhaustive coverage.
    Each source is a public URL. Never send private index or exclusions to provider.
    """
    visited=set()
    for item in plan:
        url=canonical_url(item['url']); op=item.get('operation','catalog')
        row={'id':item['id'],'url':url,'operation':op,'scope':item.get('scope','bounded'),'status':'pending'}
        if not url or (url,op) in visited:
            row.update(status='skipped',reason='invalid_or_duplicate_url'); ledger.append(row); continue
        visited.add((url,op)); candidates=[]
        try:
            if op=='catalog': raw=provider.extract(url,CATALOG_SCHEMA,CATALOG_PROMPT)
            elif op=='crawl': raw=provider.crawl(url,item.get('limit',3),item.get('include_paths'))
            elif op=='map': raw=provider.map(url,item.get('limit',50),item.get('search'))
            else: raise ValueError('Unsupported catalog operation')
            row['response']=raw
            if raw.get('body_error') or raw.get('error') or raw.get('success') is False or (raw.get('metadata') or {}).get('statusCode',200)>=400 or raw.get('status') in ('failed','cancelled'):
                row.update(status='failed',reason=str(raw.get('body_error') or raw.get('error') or raw.get('status') or 'HTTP error'))
            else:
                candidates=catalog_titles(raw)
                # Map enumerates links only; require explicit catalog title/path metadata.
                if op=='map':
                    links=raw.get('links') or (raw.get('data') or {}).get('links',[])
                    prefix=item.get('candidate_path_prefix','')
                    candidates=[{'title':r['title'],'url':r['url']} for r in links if isinstance(r,dict) and r.get('title') and r.get('url') and prefix and prefix in r['url']]
                row.update(status='partial' if raw.get('next') or raw.get('partial') or raw.get('status') not in (None,'completed') else 'retrieved',candidate_count=len(candidates),coverage_complete=False)
        except Exception as exc: row.update(status='failed',reason=str(exc))
        ledger.append(row)
        yield {'id':item['id'],'source':url,'candidates':[{**c,'catalog_source':url,'metadata_unverified':True} for c in candidates if title_key(c.get('title'))]}


def run_catalog_round(index, crosswalk, provider, plan, verify, target=5, min_runtime=80):
    coverage=[]; wrapped=CatalogIndex(index,crosswalk)
    seen=set()
    def batches():
        for batch in catalog_batches(provider,plan,coverage):
            unique=[]; duplicates=0
            for c in batch['candidates']:
                reviewed=crosswalk.resolve(c)
                key=reviewed.get('production_id') or title_key(c.get('title'))
                if key in seen: duplicates+=1; continue
                seen.add(key); unique.append(c)
            coverage[-1]['crosswalk_duplicates']=duplicates
            yield {**batch,'candidates':unique}
    result=run_round(wrapped,batches(),verify,
                     min_runtime,target,identity_review=crosswalk.resolve)
    result['coverage']=coverage
    result['coverage_complete']=False
    return result


class ConnectorReplayTransport:
    """Replay recorded public connector projections, never invent missing responses."""
    def __init__(self, receipts):
        self.receipts=receipts; self.calls=[]
    def __call__(self,operation,args):
        selector=args.get('query',args.get('url'))
        matches=[r for r in self.receipts if r['operation']==operation and r['selector']==selector]
        if len(matches)!=1: raise RuntimeError('Missing or ambiguous connector receipt: '+str(selector))
        self.calls.append({'operation':operation,'selector':selector,'receipt_id':matches[0].get('receipt_id')})
        return matches[0]['response']

def main():
    p=argparse.ArgumentParser(description='Catalog-first BL Engine discovery')
    for key in ('checkpoint','workbook','history-archive','plan','crosswalk','reviews','output'):
        p.add_argument('--'+key,required=True)
    p.add_argument('--extra-workbook',action='append',default=[])
    p.add_argument('--replay'); p.add_argument('--target',type=int,default=5); p.add_argument('--min-runtime',type=int,default=80)
    a=p.parse_args(); read=lambda f:json.loads(Path(f).read_text(encoding='utf-8'))
    index=build_index(read(a.checkpoint),a.workbook,load_history_archive(a.history_archive),a.extra_workbook)
    cw=Crosswalk()
    for row in read(a.crosswalk): cw.add(row)
    transport=ConnectorReplayTransport(read(a.replay)) if a.replay else rest_transport
    provider=FirecrawlProvider(transport); reviews=read(a.reviews)
    def verify(candidate):
        review=reviews.get(candidate.get('production_id'),{})
        return public_evidence(provider,candidate,review.get('urls',[]),lambda item:{**item,**review.get('reviewed',{})})
    result=run_catalog_round(index,cw,provider,read(a.plan),verify,a.target,a.min_runtime)
    result.update(mode='live-connector-projection-replay' if a.replay else 'rest',
        inputs={Path(x).name:digest(x) for x in [a.checkpoint,a.workbook,a.history_archive,*a.extra_workbook,a.plan,a.crosswalk,a.reviews,*([a.replay] if a.replay else [])]},
        connector_calls=getattr(transport,'calls',[]),limitations=['Bounded catalogs; no exhaustive coverage claim.','Reviewed source assertions are required; unmatched does not mean novel.','Connector projection replay is not a deployed autonomous connector runtime.'])
    path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:len(result[k]) for k in ('coverage','excluded','quarantine','researched','recommendations')}))

if __name__=='__main__': main()
