"""R91 quarantine resolution and live-connector contract for BL ENGINE.

Public research may resolve a production identity or prove it is out of scope, but it
never mutates private canonical history.  Private overlays are applied only to the
in-memory exclusion index and remain outside the public repository.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit
import json
from .firecrawl_research import title_key, names

SCOPE_CLASSES={
    "target_male_male_live_action", "non_bl", "female_female", "animation",
    "documentary", "erotic_or_adult", "wrong_region", "unknown"
}
RELATIONS={"same","sequel","special","remake","edit"}


def canonical_source_url(url):
    if not isinstance(url,str): return ""
    p=urlsplit(url)
    if p.scheme not in ("http","https") or not p.hostname: return ""
    return urlunsplit((p.scheme,p.netloc.lower(),p.path.rstrip("/") or "/",p.query,""))


def valid_reviewed_source(source):
    return (isinstance(source,dict) and source.get("reviewed") is True and
            bool(canonical_source_url(source.get("url"))) and bool(source.get("excerpt")))


@dataclass
class ResolutionRegistry:
    """Reviewed public identity resolutions for previously quarantined catalog rows.

    `production_id` must be an attributable external identifier: provider id/slug,
    official program id, or canonical source URL.  It is not an engine-generated id.
    """
    rows:list=field(default_factory=list)
    def add(self,row):
        row=dict(row)
        if not title_key(row.get("title")): raise ValueError("resolution title required")
        if row.get("scope_class") not in SCOPE_CLASSES: raise ValueError("invalid scope class")
        if not row.get("production_id"): raise ValueError("attributable production_id required")
        if not row.get("production_id_type"): raise ValueError("production_id_type required")
        if not valid_reviewed_source(row.get("source")): raise ValueError("reviewed source required")
        relation=row.get("relation","same")
        if relation not in RELATIONS: raise ValueError("invalid relation")
        if relation in {"sequel","special","remake","edit"} and not title_key(row.get("parent_title")):
            raise ValueError("parent_title required for related production")
        row["relation"]=relation
        row["aliases"]=names(row.get("aliases"))
        self.rows.append(row)
    def matching(self,candidate):
        keys={title_key(x) for x in [candidate.get("title"),*names(candidate.get("aliases"))]}-{""}
        return [r for r in self.rows if keys & ({title_key(r["title"]),*map(title_key,r.get("aliases",[]))}-{""})]
    def one(self,candidate):
        matches=self.matching(candidate)
        ids={r["production_id"] for r in matches}
        if not matches:return None
        if len(ids)!=1:return {"state":"collision","matches":matches}
        return {"state":"resolved","row":matches[0],"matches":matches}
    def enrich(self,candidate):
        hit=self.one(candidate)
        if not hit or hit["state"]!="resolved": return dict(candidate)
        r=hit["row"]
        out={**candidate,
             "aliases":list(dict.fromkeys([*names(candidate.get("aliases")),r["title"],*r.get("aliases",[])])),
             "production_id":r["production_id"],"production_id_type":r["production_id_type"],
             "scope_class":r["scope_class"],"resolution_source":r["source"]["url"],
             "relation":r.get("relation","same"),"parent_title":r.get("parent_title"),
             "identity_verified_new":r.get("reviewed_novel") is True,
             "identity_review_sources":list(dict.fromkeys([*candidate.get("identity_review_sources",[]),r["source"]["url"]]))}
        for k in ("country","year","format","runtime_minutes"):
            if k in r: out[k]=r[k]
        return out


class R91Index:
    """Resolution layer in front of the existing private R90 catalog index."""
    def __init__(self,base,registry):self.base=base;self.registry=registry
    def __getattr__(self,name):return getattr(self.base,name)
    def check(self,candidate):
        hit=self.registry.one(candidate)
        if hit and hit["state"]=="collision":
            return {"state":"quarantine","reason":"resolution_collision",
                    "matches":[r["production_id"] for r in hit["matches"]]}
        if hit:
            r=hit["row"]
            if r.get("accounted_for") is True:
                return {"state":"known","reason":"recovered_accounted_identity","resolution":r,"effective":{}}
            if r["scope_class"]!="target_male_male_live_action":
                return {"state":"known","reason":"verified_out_of_scope:"+r["scope_class"],"resolution":r,"effective":{}}
            if r.get("relation")=="edit":
                return {"state":"known","reason":"alternate_edit_not_new","resolution":r,"effective":{}}
            candidate=self.registry.enrich(candidate)
        result=self.base.check(candidate)
        if (hit and hit.get('state')=='resolved' and result.get('state')=='quarantine' and
            result.get('reason')=='fuzzy_identity_review'):
            r=hit['row']
            if r.get('relation') in {'sequel','special','remake'} and r.get('reviewed_novel') is True:
                parent=title_key(r.get('parent_title'))
                parent_records=getattr(self.base,'by_key',{}).get(parent,[])
                parent_keys={parent}
                for record in parent_records:
                    parent_keys.update(title_key(n) for n in [record.get('title',''),*record.get('aliases',[])])
                if parent_records and set(result.get('matches',[])) <= parent_keys:
                    return {'state':'unresolved','reason':'verified_distinct_related_production_parent_only'}
        return result


def apply_private_overlay(index,rows):
    """Add explicit prior user facts to the in-memory blocker only; never rewrite checkpoint."""
    for i,row in enumerate(rows or []):
        if not title_key(row.get("title")): raise ValueError("overlay title required")
        if row.get("explicit") is not True: raise ValueError("overlay must be explicit user history")
        index.add(row["title"],names(row.get("aliases")),source="r91/private-overlay",
                  status=row.get("status"),score=row.get("score"),country=row.get("country"),
                  year=row.get("year"),priority=6,order=i)
    return index


def resolve_prior_quarantine(prior_rows,registry,index):
    """Audit the R90 quarantine without treating out-of-scope media as canonical watches."""
    out={"resolved_accounted":[],"resolved_out_of_scope":[],"target_survivors":[],"unresolved":[],"collisions":[]}
    wrapped=R91Index(index,registry)
    for entry in prior_rows:
        c=entry.get("candidate",entry)
        hit=registry.one(c)
        if not hit:
            out["unresolved"].append(entry);continue
        if hit["state"]=="collision":out["collisions"].append({**entry,"resolution":hit});continue
        r=hit["row"]
        if r.get("accounted_for") is True:
            out["resolved_accounted"].append({**entry,"resolution":r});continue
        if r["scope_class"]!="target_male_male_live_action" or r.get("relation")=="edit":
            out["resolved_out_of_scope"].append({**entry,"resolution":r});continue
        enriched=registry.enrich(c); state=wrapped.check(enriched)
        if state["state"]=="known": out["resolved_accounted"].append({**entry,"resolution":r,"identity":state})
        elif state["state"]=="unresolved": out["target_survivors"].append({**entry,"resolution":r,"candidate":enriched})
        else: out["collisions"].append({**entry,"resolution":r,"identity":state})
    return out


def _json_line(stdout):
    for line in reversed((stdout or "").splitlines()):
        line=line.strip()
        if not line:continue
        try:return json.loads(line)
        except Exception:continue
    return None


def interact_titles(response):
    """Normalize the actual Firecrawl interact envelope used for catalog pagination."""
    if not isinstance(response,dict) or response.get("success") is not True:
        raise ValueError("unsuccessful interact response")
    value=_json_line(response.get("stdout"))
    if not isinstance(value,list) or not all(isinstance(x,str) and x.strip() for x in value):
        raise ValueError("interact response did not contain a JSON title list")
    return list(dict.fromkeys(x.strip() for x in value))


class LiveConnectorTransport:
    """Host-injected connector runtime contract.

    The repository never contains credentials.  The host supplies `invoke(operation,args)`;
    this wrapper validates a live response and records only public call metadata.
    """
    def __init__(self,invoke):self.invoke=invoke;self.calls=[]
    def __call__(self,operation,args):
        if operation not in {"search","scrape","map","crawl","interact"}:raise ValueError("unsupported live operation")
        response=self.invoke(operation,dict(args))
        if not isinstance(response,dict):raise RuntimeError("connector returned non-object")
        if response.get("success") is False or response.get("error"):
            raise RuntimeError(str(response.get("error") or "connector failure"))
        rid=(response.get("metadata") or {}).get("scrapeId") or response.get("scrapeId") or response.get("id")
        self.calls.append({"operation":operation,"selector":args.get("url") or args.get("query"),"receipt_id":rid})
        return response
