"""ATLAS Deep Discovery evidence gate. Offline and dependency-free.

Research workers supply evidence JSON; this module never claims to have browsed
or verified URLs itself. A missing proof is not a positive result.
"""
import argparse, json, re, sys
from pathlib import Path

BLOCKED={"watched","completed","dropped","skip","reject","avoid","already tracked",
         "interested","maybe","plan","watching","caught up","previously dropped"}

def key(value):
    return "".join(c for c in str(value).casefold() if c.isalnum())

def exclusion_index(rows):
    out={}
    for row in rows:
        status=str(row.get("status","")).casefold()
        if any(b in status for b in BLOCKED):
            for title in [row.get("title",""),*row.get("aliases",[])]:
                if key(title): out[key(title)]=status
    return out

def review(candidate, exclusions):
    blockers=[]
    identity=[candidate.get("title",""),*candidate.get("aliases",[])]
    matches=[exclusions[key(t)] for t in identity if key(t) in exclusions]
    if matches: blockers.append("known_title:"+matches[0])
    if not candidate.get("released"): blockers.append("release_unverified")
    if not candidate.get("central_mm_romance"): blockers.append("central_romance_unverified")
    if not candidate.get("healthy_consent"): blockers.append("consent_unverified")
    if not candidate.get("actual_gender_confusion"): blockers.append("trope_unverified")
    if not candidate.get("romantic_payoff"): blockers.append("payoff_unverified")
    stream=candidate.get("stream") or {}
    if not (stream.get("official_url","").startswith("https://") and
            stream.get("region_verified") and stream.get("english_subtitles_verified")):
        blockers.append("stream_unverified")
    sources=candidate.get("sources") or []
    if not any(str(s).startswith("https://") for s in sources):
        blockers.append("missing_evidence")
    return {"title":candidate.get("title"),"disposition":"verified_candidate" if not blockers else "blocked","blockers":blockers}

def run(payload):
    exclusions=exclusion_index(payload.get("known_titles",[]))
    results=[review(x,exclusions) for x in payload.get("candidates",[])]
    return {"schema_version":1,"results":results,"verified":sum(x["disposition"]=="verified_candidate" for x in results),
            "warning":"Evidence gate validates presence of research receipts, not truth of source claims. Independent source review required."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path,help="JSON with known_titles and candidates")
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    result=run(json.loads(args.input.read_text(encoding="utf-8")))
    output=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: args.output.write_text(output+"\n",encoding="utf-8")
    else: print(output)
    return 0
if __name__=="__main__":sys.exit(main())
