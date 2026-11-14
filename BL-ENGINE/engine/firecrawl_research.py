"""BL Engine research adapter: private identity gate before public evidence work.

The host may inject a Firecrawl connector transport; REST is available for CLI use.
Neither provider receives private histories, statuses, ratings or exclusion lists.
"""
from __future__ import annotations
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
import hashlib
import argparse
import json
import os
import re
import time
from .identity import normalize
from .workbook import _rows, NS, PKG
from .evidence import evidence_gate
from .ranking import triage

BAD = {"", "#NAME?", "#REF!", "#VALUE!", "ENGINE COMMAND"}
SHEETS = {
    "WATCH": ("A", None, "B", "C", "E", "G"),
    "Alias Map": ("A", "B", None, None, None, None),
    "Manual Overrides": ("A", "B", "C", None, None, None),
    "Rejected Log": ("C", None, "D", None, None, None),
    "Oct 2026 Overrides": ("A", None, "B", None, None, None),
    "Viewing Reconciliation 2026": ("A", None, "B", None, None, None),
    "Feedback 2026-10-27": ("A", None, "B", None, None, None),
    "Canonical Audit Log": ("A", None, "C", None, None, None),
    "Status Review Queue": ("A", None, None, None, None, None),
    "Candidate Catalog": ("A", "C", None, "D", "E", None),
    "Live Candidate Intake": ("A", "C", None, "D", "E", None),
    "Concrete Vibe Check": ("A", None, None, None, None, None),
    "Known Title Index": ("B", "C", "E", "F", "G", None),
    "Known Index": ("B", None, "C", None, None, None),
    "Corrections": ("A", None, "B", None, None, None),
    "Audit Candidates": ("A", None, None, None, None, None),
    "R43 Strict Search": ("A", None, None, None, None, None),
}

def title_key(value):
    return normalize(value) if isinstance(value, str) and value.strip() not in BAD else ""

def names(value):
    if isinstance(value, list): return [x for x in value if title_key(x)]
    if not title_key(value): return []
    # Preserve raw strings and explicitly delimited alternatives; never use formula keys.
    return list(dict.fromkeys([value,*[v.strip() for v in re.split(r"\s+/\s+|[;\n|]",value) if title_key(v.strip())]]))

def year_value(value):
    try: return int(float(value))
    except (TypeError, ValueError): return None

def score_value(value):
    try: return float(value)
    except (TypeError, ValueError): return None

def workbook_rows(path):
    """Use existing safe XML row parser; include all identity-bearing sheets."""
    with ZipFile(path) as archive:
        strings=[]
        if "xl/sharedStrings.xml" in archive.namelist():
            root=ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings=["".join(t.text or "" for t in row.findall(".//m:t",NS)) for row in root.findall("m:si",NS)]
        rels={r.attrib["Id"]:r.attrib["Target"] for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels")).findall("{"+PKG+"}Relationship")}
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall(".//m:sheet",NS):
            name=sheet.attrib["name"]
            if name not in SHEETS: continue
            target=rels[sheet.attrib["{"+NS["r"]+"}id"]].lstrip("/")
            if not target.startswith("xl/"): target="xl/"+target
            yield name, list(_rows(archive,target,strings))[1:]

class IdentityIndex:
    def __init__(self): self.by_key=defaultdict(list); self.counts=defaultdict(int); self.reference_keys=defaultdict(set)
    def add(self,title,aliases=(),source="unknown",status=None,score=None,country=None,year=None,priority=0,order=0):
        if not title_key(title): return
        record=dict(title=title, aliases=names(list(aliases)), source=source, status=status,
                    score=score_value(score), country=country, year=year_value(year),priority=priority,order=order)
        self.counts[source]+=1
        for key in {title_key(n) for n in [title,*record["aliases"]]}-{ "" }:
            self.by_key[key].append(record)
    def check(self,candidate):
        keys={title_key(n) for n in [candidate.get("title"),*names(candidate.get("aliases"))]}-{""}
        if not keys: return {"state":"quarantine","reason":"missing_title"}
        exact=[]
        for key in sorted(keys):
            for record in self.by_key.get(key,[]):
                if record not in exact: exact.append(record)
        if exact:
            # Follow explicit alias-to-canonical edges for status provenance, without merging records.
            for record in list(exact):
                for linked in self.by_key.get(title_key(record["title"]),[]):
                    if linked not in exact: exact.append(linked)
            # An exact collision is never novel, even when metadata differs.
            return {"state":"known","reason":"exact_or_alias","matches":exact,"effective":self.effective(exact)}
        references=sorted({sheet for key in keys for sheet in self.reference_keys.get(key,[])})
        if references: return {"state":"known","reason":"historical_reference_requires_review","matches":references,"effective":{"status":None,"score":None,"source":None}}
        near=set()
        for key in keys:
            if len(key)<6: continue
            for other in self.by_key:
                if len(other)>=6 and abs(len(other)-len(key))<=max(len(other),len(key))*0.24 and SequenceMatcher(None,key,other).ratio()>=0.88:
                    near.add(other)
        if near: return {"state":"quarantine","reason":"fuzzy_identity_review","matches":sorted(near)}
        return {"state":"unresolved","reason":"no_recovered_match"}
    @staticmethod
    def effective(matches):
        stated=[r for r in matches if r.get("status")]
        if not stated: return {"status":None,"score":None,"source":None}
        # Different production metadata: block freshness, but don't merge statuses.
        productions={(r['country'],r['year']) for r in stated if r.get('country') and r.get('year')}
        if len(productions)>1: return {"status":"identity_conflict","score":None,"source":None}
        # Later explicit user deltas supersede workbook events; duplicate WATCH rows are not later corrections.
        top=max(r["priority"] for r in stated); rows=[r for r in stated if r["priority"]==top]
        if top>=4: chosen=max(rows,key=lambda r:r["order"])
        else:
            complete=[r for r in rows if str(r["status"]).casefold().startswith("completed")]
            planned=lambda r:str(r["status"]).casefold().startswith(("plan","waiting","maybe"))
            if complete and all(r in complete or planned(r) for r in rows): chosen=complete[0]
            elif len({str(r["status"]).casefold() for r in rows})==1: chosen=rows[0]
            else: return {"status":"status_conflict","score":None,"source":None}
        return {k:chosen[k] for k in ("status","score","source")}

def build_index(checkpoint,workbook=None,historical=None,extra_workbooks=()):
    idx=IdentityIndex()
    for i,r in enumerate(checkpoint.get("watch",[])):
        idx.add(r.get("Title"),source="checkpoint/WATCH",status=r.get("Status"),score=r.get("Score"),country=r.get("Country"),year=r.get("Year"),priority=1,order=i)
    for r in checkpoint.get("aliases",[]): idx.add(r.get("Canonical Title"),names(r.get("Alias")),source="checkpoint/Alias Map")
    for i,r in enumerate(checkpoint.get("manual_overrides",[])):
        idx.add(r.get("Title"),names(r.get("Alias")),source="checkpoint/Manual Overrides",status=r.get("Status"),priority=3,order=i)
    for i,r in enumerate(checkpoint.get("explicit_deltas",[])):
        roundnum=re.search(r"\bR(\d+)\b",str(r.get("source","")))
        idx.add(r.get("title"),names(r.get("aliases")),source="checkpoint/explicit",status=r.get("status"),score=r.get("rating"),country=r.get("region"),year=r.get("year"),priority=5,order=(int(roundnum.group(1)) if roundnum else 10000)*1000+i)
    def walk(obj,source):
        if isinstance(obj,dict):
            if obj.get("title"): idx.add(obj["title"],names(obj.get("aliases")),source=source,country=obj.get("country") or obj.get("region"),year=obj.get("year"))
            for key in ("titles", "r77_display", "canonical_title"):
                for title in names(obj.get(key)): idx.add(title,source=source)
            for value in obj.values():
                if isinstance(value,(dict,list)): walk(value,source)
        elif isinstance(obj,list):
            for value in obj: walk(value,source)
    for section in ("research_discovery_log","r77_research_only","r77_canonical_collisions"):
        walk(checkpoint.get(section,[]),"checkpoint/"+section)
    if workbook:
        for sheet,rows in workbook_rows(workbook):
            title,alias,status,country,year,score=SHEETS[sheet]
            for i,r in enumerate(rows):
                priority=1 if sheet=="WATCH" else 3 if sheet in ("Manual Overrides","Rejected Log","Oct 2026 Overrides","Viewing Reconciliation 2026","Feedback 2026-10-27","Canonical Audit Log") else 0
                idx.add(r.get(title),names(r.get(alias)),source="workbook/"+sheet,status=r.get(status),score=r.get(score),country=r.get(country),year=r.get(year),priority=priority,order=i)
    if historical:
        add_history(idx,historical)
    for extra in extra_workbooks:
        for sheet,rows in workbook_rows(extra):
            title,alias,status,country,year,score=SHEETS[sheet]
            for i,r in enumerate(rows):
                idx.add(r.get(title),names(r.get(alias)),source="earlier/"+Path(extra).name+"/"+sheet,status=r.get(status),score=r.get(score),country=r.get(country),year=r.get(year),priority=0,order=i)
    if not idx.counts["checkpoint/WATCH"]: raise ValueError("No WATCH records; fail closed")
    expected=checkpoint.get("canonical_baseline",{})
    for field,section in [("watch_count","WATCH"),("alias_count","Alias Map"),("manual_override_count","Manual Overrides")]:
        if expected.get(field) is not None and idx.counts["checkpoint/"+section]!=expected[field]:
            raise ValueError("Checkpoint count mismatch: "+section)
    if workbook and idx.counts["workbook/WATCH"]!=idx.counts["checkpoint/WATCH"]: raise ValueError("Workbook/checkpoint WATCH count mismatch; reconcile first")
    return idx

# Header matching only for historical title-bearing fields; never fuzzy-match prose or formulas.
TITLE_HEADERS={"title","english title","canonical title","canonical identity","title / identity","title / aliases","title / alias","title / original alias","title / native identity","title / alternate identity","title / alternate title","title / name","title / lane","title(s)","title / original","name / alias","display title","user-facing title","already watched title","candidate","candidate / aliases","candidate / alias","candidate title","lead","series","identity","identity / canonical key","primary key","title(s)"}
ALIAS_HEADERS={"alias","aliases","native title","original title","english alias","native / alternate title","native / alternate titles","other aliases","original / alias","native / alternate identity","original / alternate title","alias / identity","aliases / original","alias / secondary key","alias or release identity","native / alternate title","title / alias","title / aliases"}

def add_history(index,history):
    """R78 reconciled archive is append-only provenance, not a replacement WATCH."""
    for i,r in enumerate(history.get("watch_records",[])):
        index.add(r.get("Title"),source="history/WATCH",status=r.get("Status"),score=r.get("Score"),country=r.get("Country"),year=r.get("Year"),priority=0,order=i)
    for i,r in enumerate(history.get("latest_explicit_overlay",[])):
        index.add(r.get("title"),source="history/explicit_overlay",status=r.get("status"),score=r.get("explicit_score"),priority=4,order=i)
    for sheet,rows in history.get("source_sheets",{}).items():
        if not rows: continue
        base=sheet.split(":")[-1]
        header=[str(v or "").strip().casefold() for v in rows[0]]
        cols=[i for i,h in enumerate(header) if h in TITLE_HEADERS]
        als=[i for i,h in enumerate(header) if h in ALIAS_HEADERS and i not in cols]
        if not cols: continue
        for r in rows[1:]:
            if not isinstance(r,list): continue
            vals=[r[i] for i in cols if i<len(r) and title_key(r[i]) and len(r[i])<=250]
            aliases=[r[i] for i in als if i<len(r) and title_key(r[i]) and len(r[i])<=250]
            # Keep separate title fields as independent blockers. Do not treat all cells as aliases.
            for title in vals:
                index.add(title,[*names(title)[1:],*aliases] if len(vals)==1 else names(title)[1:],source="history/sheet/"+base)
    # Preserve exact historical cell references (including nonstandard title columns), but don't fuzzy-match prose.
    for sheet,rows in history.get("source_sheets",{}).items():
        for row in rows:
            for v in row if isinstance(row,list) else []:
                if title_key(v) and 2<=len(v)<=160 and not v.startswith(("http", "=", "#")):
                    index.reference_keys[title_key(v)].add(sheet)


class FirecrawlProvider:
    """Transport receives public operation name and arguments; supports MCP or REST."""
    def __init__(self,transport): self.transport=transport
    def search(self,query,limit=20): return self.transport("search",{"query":query,"limit":limit,"sources":["web"],"objective":"Discover production identities, not recommendations."})
    def map(self,url,limit=100,search=None):
        args={"url":url,"limit":limit};
        if search: args["search"]=search
        return self.transport("map",args)
    def crawl(self,url,limit=5,include_paths=None):
        args={"url":url,"limit":limit,"maxDiscoveryDepth":1,"allowExternalLinks":False,"allowSubdomains":False,"scrapeOptions":{"formats":["json"],"jsonOptions":{"schema":CATALOG_SCHEMA,"prompt":CATALOG_PROMPT}}}
        if include_paths: args["includePaths"]=include_paths
        return self.transport("crawl",args)
    def extract(self,url,schema,prompt): return self.transport("scrape",{"url":url,"formats":["markdown","json"],"jsonOptions":{"schema":schema,"prompt":prompt},"objective":"Extract public production facts with source evidence; use null if absent."})

def rest_transport(operation,args):
    """Firecrawl v2 HTTP transport; FIRECRAWL_API_KEY is never logged."""
    key=os.environ.get("FIRECRAWL_API_KEY")
    if not key: raise RuntimeError("FIRECRAWL_API_KEY missing; use host connector transport")
    base="https://api.firecrawl.dev/v2/"; payload=dict(args); payload.pop("objective",None)
    def convert(options):
        if "jsonOptions" in options:
            options["formats"]=[f for f in options.get("formats",[]) if f!="json"]+[{"type":"json",**options.pop("jsonOptions")}]
    if operation=="scrape": convert(payload)
    if operation=="crawl": convert(payload.get("scrapeOptions",{}))
    def request(url,data=None):
        if urlsplit(url).hostname!="api.firecrawl.dev": raise ValueError("Unexpected Firecrawl API host")
        req=Request(url,data=json.dumps(data).encode() if data is not None else None,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        with urlopen(req,timeout=60) as response: return json.load(response)
    result=request(base+operation,payload)
    if operation=="crawl" and result.get("id"):
        for _ in range(12):
            result=request(base+"crawl/"+result["id"])
            if result.get("status") in ("completed","failed","cancelled"): break
            time.sleep(2)
    return result

CATALOG_PROMPT="Extract explicitly listed live-action Japanese and Korean production identities only: title, native/English aliases, year, country and detail URL. Do not invent or infer aliases or include manga/anime. No plot analysis."
CATALOG_SCHEMA={"type":"object","properties":{"titles":{"type":"array","items":{"type":"object","properties":{"title":{"type":"string"},"aliases":{"type":"array","items":{"type":"string"}},"year":{"type":"integer"},"country":{"type":"string"},"url":{"type":"string"}},"required":["title"]}}},"required":["titles"]}
FACT_SCHEMA={"type":"object","properties":{"title":{"type":"string"},"runtime_minutes":{"type":"number"},"format":{"type":"string"},"claims":{"type":"array","items":{"type":"object","properties":{"fact":{"type":"string"},"supported":{"type":"boolean"},"quote":{"type":"string"},"source_url":{"type":"string"}},"required":["fact","supported","quote","source_url"]}}},"required":["title","claims"]}

def strict_gate(candidate,min_runtime=80):
    reasons=list(evidence_gate(candidate)["reasons"])
    if candidate.get("country") not in ("Japan","South Korea"): reasons.append("region")
    if not isinstance(candidate.get("runtime_minutes"),(int,float)) or candidate["runtime_minutes"]<min_runtime: reasons.append("substantial_runtime")
    if candidate.get("format") not in ("series","feature"): reasons.append("format")
    for fact in ("happy_ending","mutual_romance","cozy_fit","non_erotic","non_coercive","substantial_format"):
        claim=candidate.get("evidence",{}).get(fact,{})
        if not isinstance(claim,dict) or claim.get("supported") is not True or not any(isinstance(s,str) and s.startswith("https://") for s in claim.get("sources",[])): reasons.append("unsupported:"+fact)
    if candidate.get("identity_verified_new") is not True or not candidate.get("identity_review_sources"): reasons.append("identity_review_required")
    if candidate.get("evidence_reviewed") is not True: reasons.append("evidence_review_required")
    if candidate.get("starts_established") is not False: reasons.append("new_relationship_buildup_unverified")
    return {"approved":not reasons,"reasons":reasons}

def run_round(index,batches,verify,min_runtime=80,target=5,identity_review=None):
    """Consume distinct public candidate batches lazily; gate BEFORE verify. No quota padding."""
    receipts=[]; excluded=[]; quarantine=[]; researched=[]; accepted=[]; seen=set()
    for batch in batches:
        counts=defaultdict(int)
        for candidate in batch["candidates"]:
            key=title_key(candidate.get("title"))
            if key and key in seen: counts["duplicate_batch"]+=1; continue
            if key: seen.add(key)
            match=index.check(candidate); counts[match["state"]]+=1
            entry={"candidate":candidate,"identity":match,"source_batch":batch["id"]}
            if match["state"]=="known": excluded.append(entry); continue
            if match["state"]!="unresolved": quarantine.append(entry); continue
            try: candidate=identity_review(candidate) if identity_review is not None else candidate
            except Exception as exc:
                entry["review_error"]=str(exc); quarantine.append(entry); continue
            updated=index.check(candidate); entry["reviewed_identity"]=updated
            if updated["state"]=="known": excluded.append(entry); continue
            if updated["state"]!="unresolved" or candidate.get("identity_verified_new") is not True or not candidate.get("identity_review_sources"):
                quarantine.append(entry); continue
            try: enriched=verify(candidate)
            except Exception as exc: enriched={**candidate,"research_error":str(exc)}
            if not isinstance(enriched,dict): enriched={**candidate,"research_error":"invalid evidence response"}
            enriched={**candidate,**enriched}
            # New native names from evidence must pass the gate again.
            post=index.check(enriched)
            gate=strict_gate(enriched,min_runtime)
            if post["state"]!="unresolved": gate={"approved":False,"reasons":["identity_recheck"]+gate["reasons"]}
            entry.update(evidence=enriched,post_identity=post,gate=gate); researched.append(entry)
            if gate["approved"]:
                # Existing v3 evidence and ranking remain the final gate.
                ranked=triage([enriched],[],[])
                if ranked["recommendations"]: accepted.append(ranked["recommendations"][0])
            if len(accepted)>=target: break
        receipts.append({"id":batch["id"],"query":batch.get("query"),"source":batch.get("source"),"counts":dict(counts),"candidate_count":len(batch["candidates"])})
        if len(accepted)>=target: break
    return {"receipts":receipts,"excluded":excluded,"quarantine":quarantine,"researched":researched,"recommendations":accepted,"source_counts":dict(index.counts),"identity_key_count":len(index.by_key),"historical_reference_key_count":len(index.reference_keys)}

def load_history_archive(path):
    with ZipFile(path) as z:
        name="R78_reconciled_history.json"; payload=z.read(name); manifest=json.loads(z.read("manifest.json"))
        if hashlib.sha256(payload).hexdigest()!=manifest["files"][name]: raise ValueError("Historical archive hash mismatch")
        return json.loads(payload)

def response_data(result):
    return result.get("data",result) if isinstance(result,dict) else {}

def catalog_titles(result):
    data=response_data(result)
    if isinstance(data,dict): return (data.get("json") or result.get("json") or {}).get("titles",[])
    if isinstance(data,list): return [title for page in data if isinstance(page,dict) for title in (page.get("json") or {}).get("titles",[])]
    return []

def live_batches(provider,plan,receipts):
    """A bounded sequence of public catalog operations. Search/map only discover URLs;
    the plan selects catalog paths, not individual titles. Crawl stays at catalog scope.
    """
    for item in plan:
        op=item["operation"]; urls=[]; candidates=[]
        if op=="search":
            raw=provider.search(item["query"],item.get("limit",12)); data=response_data(raw)
            hits=data.get("web",[]) if isinstance(data,dict) else data
            urls=[r.get("url") for r in hits if isinstance(r,dict) and r.get("url")]
        elif op=="map":
            raw=provider.map(item["url"],item.get("limit",100),item.get("search")); data=response_data(raw)
            links=data.get("links",raw.get("links",[])) if isinstance(data,dict) else data
            urls=[r.get("url") if isinstance(r,dict) else r for r in links]
            prefix=item.get("candidate_path_prefix"); pattern=item.get("title_pattern")
            if prefix and pattern:
                for r in links:
                    if not isinstance(r,dict) or prefix not in r.get("url",""): continue
                    m=re.search(pattern,r.get("title", ""))
                    if m: candidates.append({"title":m.group(1),"url":r["url"],"country":item.get("country")})
        elif op=="crawl":
            raw=provider.crawl(item["url"],item.get("limit",3),item.get("include_paths")); candidates=catalog_titles(raw)
        elif op=="catalog":
            raw=provider.extract(item["url"],CATALOG_SCHEMA,CATALOG_PROMPT); candidates=catalog_titles(raw)
        else: raise ValueError("Unsupported operation: "+op)
        receipts.append({"plan":item,"response":raw})
        # Never automatically scrape every individual search/map result: only explicit catalog URL allowlist.
        for url in item.get("catalog_urls",[]):
            if url not in urls: continue
            extra=provider.extract(url,CATALOG_SCHEMA,CATALOG_PROMPT); receipts.append({"operation":"catalog","url":url,"response":extra}); candidates.extend(catalog_titles(extra))
        yield {"id":item["id"],"query":item.get("query"),"source":item.get("url",op),"candidates":candidates}

def public_evidence(provider,candidate,urls,reviewer=None):
    """Post-identity-gate structured retrieval. Reviewer must independently validate claims.
    Never promote extraction alone to approved or fabricate a user rating.
    """
    sources=[]
    for url in urls:
        if not isinstance(url,str) or not url.startswith("https://"): continue
        raw=provider.extract(url,FACT_SCHEMA,"Extract only source-supported facts about the named production: "+candidate["title"]+". Include verbatim short evidence and source URL; use unsupported when absent. Check completion, central mutual romance, happy ending, runtime, format, explicit content, coercion and official stream.")
        sources.append({"url":url,"response":raw})
    result={**candidate,"source_receipts":sources,"evidence":{}}
    return reviewer(result) if reviewer else result

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description="ATLAS BL Engine integrated Firecrawl discovery")
    p.add_argument("--checkpoint",required=True); p.add_argument("--workbook",required=True)
    p.add_argument("--history-archive",required=True); p.add_argument("--extra-workbook",action="append",default=[])
    p.add_argument("--plan",required=True); p.add_argument("--reviews",required=True)
    p.add_argument("--replay",help="JSON list of actual connector call receipts; omit to use Firecrawl REST")
    p.add_argument("--output",required=True); p.add_argument("--target",type=int,default=5); p.add_argument("--min-runtime",type=int,default=80)
    a=p.parse_args(); read=lambda path:json.loads(Path(path).read_text(encoding="utf-8"))
    checkpoint=read(a.checkpoint); history=load_history_archive(a.history_archive)
    index=build_index(checkpoint,a.workbook,history,a.extra_workbook)
    reviews=read(a.reviews); plan=read(a.plan); raw_receipts=[]
    if a.replay:
        recorded=read(a.replay)
        def transport(op,args):
            selector=args.get("query",args.get("url"))
            for item in recorded:
                if item["operation"]==op and item["selector"]==selector: return item["response"]
            raise RuntimeError("No recorded connector receipt for requested operation")
    else: transport=rest_transport
    provider=FirecrawlProvider(transport)
    def identity_review(candidate):
        review=reviews.get("identities",{}).get(title_key(candidate["title"]),{})
        return {**candidate,**review,"aliases":list(dict.fromkeys([*names(candidate.get("aliases")),*names(review.get("aliases"))]))}
    def verify(candidate):
        review=reviews.get("evidence",{}).get(title_key(candidate["title"]),{})
        return public_evidence(provider,candidate,review.get("urls",[]),lambda item:{**item,**review.get("reviewed",{})})
    result=run_round(index,live_batches(provider,plan,raw_receipts),verify,a.min_runtime,a.target,identity_review)
    result.update(mode="live-connector-replay" if a.replay else "rest",inputs={str(Path(x).name):digest(x) for x in [a.checkpoint,a.workbook,a.history_archive,*a.extra_workbook]},provider_receipts=raw_receipts,limitations=["Identity and evidence reviewer assertions are required; unmatched does not mean new.","Regional playback not established by a catalog URL."])
    path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:len(result[k]) for k in ("receipts","excluded","quarantine","researched","recommendations")}))

if __name__=="__main__": main()

