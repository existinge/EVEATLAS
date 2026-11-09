"""BL Engine private canonical-state adapter (stdlib only).

Offline gate: no HTTP, no writes to public repository. Store personal WATCH
records and outputs in private storage, never in Git history.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from difflib import SequenceMatcher
import json
from pathlib import Path
import unicodedata

def norm(value):
    value=unicodedata.normalize("NFKC",str(value or "")).casefold()
    return "".join(c for c in value if c.isalnum())

def entry_id(title,country=None,year=None):
    return ":".join([norm(title),norm(country),str(year or "")])

def build_index(state):
    records={}
    keys=defaultdict(set)
    aliases=state.get("aliases") or []
    def add(title,status,country,year,alt,source,score=None):
        if not norm(title):return
        ident=entry_id(title,country,year)
        records.setdefault(ident,dict(title=title,status=status,country=country,
                                      year=year,score=score,source=source))
        for k in [title,*(alt or [])]:
            if norm(k):keys[norm(k)].add(ident)
    for w in state.get("watch") or []:
        title=str(w.get("Title") or "")
        alt=[str(a.get("Alias")) for a in aliases
             if norm(a.get("Canonical Title"))==norm(title) and a.get("Alias")]
        add(title,str(w.get("Status") or "unresolved"),w.get("Country"),
            w.get("Year"),alt,"WATCH",w.get("Score"))
    for r in state.get("manual_overrides") or []:
        add(str(r.get("Title") or ""),str(r.get("Status") or "MANUAL"),
            None,None,[str(r["Alias"])] if r.get("Alias") else [],
            "Manual Overrides")
    for d in state.get("explicit_deltas") or []:
        title=str(d.get("title") or "")
        if not norm(title):continue
        ident=entry_id(title,d.get("region"),d.get("year"))
        records[ident]=dict(title=title,status=d.get("status"),
                            country=d.get("region"),year=d.get("year"),
                            score=d.get("rating"),source=d.get("source"),
                            overlay=True)
        for key in [title,*(d.get("aliases") or [])]:
            if norm(key):keys[norm(key)].add(ident)
    for r in state.get("r77_research_only") or []:
        title=str(r.get("title") or "")
        alternatives=[title,*(r.get("aliases") or [])]
        # A research entry must not shadow an existing WATCH identity.
        if any(norm(key) in keys for key in alternatives):continue
        add(title,"KNOWN_RESEARCH_NO_USER_REACTION",r.get("region"),
            r.get("year"),r.get("aliases") or [],"Research intake")
    return {"records":records,"keys":{k:sorted(v) for k,v in keys.items()}}

def check_candidate(candidate,index,threshold=0.89):
    title=str(candidate.get("title") or "")
    alternatives=[title,*(candidate.get("aliases") or [])]
    if not norm(title):
        return {"title":title,"gate":"IDENTITY_UNRESOLVED","reason":"missing_title"}
    matched=sorted({i for k in alternatives for i in index["keys"].get(norm(k),[])})
    if len(matched)>1:
        return {"title":title,"gate":"IDENTITY_UNRESOLVED",
                "reason":"multiple_exact_or_alias_matches","matches":matched}
    if matched:
        record=index["records"][matched[0]]
        return {"title":title,"gate":"KNOWN_TRACKED","status":record["status"],
                "reason":"canonical_title_or_alias_match","matches":matched}
    fuzzy=[]
    for k,ids in index["keys"].items():
        if len(k)<6 or len(norm(title))<6:continue
        if SequenceMatcher(None,k,norm(title)).ratio()>=threshold:
            fuzzy.extend(ids)
    if fuzzy:
        return {"title":title,"gate":"IDENTITY_UNRESOLVED",
                "reason":"possible_fuzzy_duplicate","matches":sorted(set(fuzzy))}
    if candidate.get("canonical_source_complete") is not True:
        return {"title":title,"gate":"UNVERIFIED_NOVELTY",
                "reason":"full_canonical_coverage_not_proven"}
    return {"title":title,"gate":"NOVEL_CANDIDATE",
            "reason":"no_known_title_or_alias_collision; story facts still require verification"}

def run(state,candidates=None,feedback=None):
    effective=dict(state)
    if feedback:
        allowed={"title","status","year","region","rating","source",
                 "comment","aliases","rating_scope"}
        clean=[{k:v for k,v in d.items() if k in allowed}
               for d in feedback if d.get("title") and d.get("status")]
        effective["explicit_deltas"]=[*(state.get("explicit_deltas") or []),*clean]
    index=build_index(effective)
    return {"schema_version":"1.0.0","mode":"local_private_adapter",
            "identity_count":len(index["records"]),
            "duplicate_keys_count":sum(len(v)>1 for v in index["keys"].values()),
            "applied_feedback_count":len(feedback or []),
            "candidate_audit":[check_candidate(x,index) for x in (candidates or [])],
            "warnings":["NOT ATLAS discovery execution",
                        "Does not independently authenticate web evidence or endings",
                        "Never publish private canonical data in public EVEATLAS"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state",required=True,type=Path)
    p.add_argument("--candidates",type=Path)
    p.add_argument("--feedback",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    def load(path):
        return json.loads(path.read_text(encoding="utf-8")) if path else None
    data=run(load(args.state),load(args.candidates),load(args.feedback))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
