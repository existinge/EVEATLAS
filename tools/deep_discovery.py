"""ATLAS Deep Discovery evidence gate. Offline and dependency-free.

Research workers supply evidence JSON; this module never claims to have browsed
or verified URLs itself. A missing proof is not a positive result.
"""
import argparse, json, sys
from pathlib import Path
from urllib.parse import urlsplit

BLOCKED={"watched","completed","dropped","skip","reject","avoid","already tracked",
         "interested","maybe","plan","watching","caught up","previously dropped"}
PROFILES={"broad_bl", "feminine_misidentification"}

def https_url(value):
    if not isinstance(value,str): return False
    try:
        parsed=urlsplit(value)
        return parsed.scheme=="https" and bool(parsed.hostname) and not parsed.username
    except ValueError:
        return False

def key(value):
    return "".join(c for c in str(value).casefold() if c.isalnum())

def exclusion_index(rows):
    out={}
    for row in rows:
        status=str(row.get("status","")).casefold()
        # Any supplied tracked identity is accounted for, including unresolved
        # statuses and MANUAL-SEEN. Unknown is not evidence of fresh novelty.
        for title in [row.get("title",""),*row.get("aliases",[])]:
            if key(title): out[key(title)]=status or "status_unresolved"
    return out

def review(candidate, exclusions, profile="broad_bl"):
    blockers=[]
    profile=candidate.get("discovery_profile",profile)
    if profile not in PROFILES: blockers.append("unknown_discovery_profile")
    if not key(candidate.get("title","")): blockers.append("identity_unverified")
    identity=[candidate.get("title",""),*candidate.get("aliases",[])]
    matches=[exclusions[key(t)] for t in identity if key(t) in exclusions]
    if matches: blockers.append("known_title:"+matches[0])
    if candidate.get("released") is not True: blockers.append("release_unverified")
    if candidate.get("central_mm_romance") is not True: blockers.append("central_romance_unverified")
    if candidate.get("healthy_consent") is not True: blockers.append("consent_unverified")
    if profile=="feminine_misidentification":
        if not (candidate.get("actual_gender_confusion") is True or
                candidate.get("feminine_presenting_male") is True):
            blockers.append("trope_unverified")
        if not any(https_url(s) for s in candidate.get("trope_evidence",[]) or []):
            blockers.append("trope_evidence_missing")
    if candidate.get("romantic_payoff") is not True: blockers.append("payoff_unverified")
    stream=candidate.get("stream") or {}
    if not (https_url(stream.get("official_url")) and
            stream.get("region_verified") is True and stream.get("english_subtitles_verified") is True):
        blockers.append("stream_unverified")
    sources=candidate.get("sources") or []
    if not any(https_url(s) for s in sources):
        blockers.append("missing_evidence")
    return {"title":candidate.get("title"),"discovery_profile":profile,
            "disposition":"verified_candidate" if not blockers else "blocked","blockers":blockers}

def run(payload):
    exclusions=exclusion_index(payload.get("known_titles",[]))
    results=[review(x,exclusions,payload.get("discovery_profile","broad_bl")) for x in payload.get("candidates",[])]
    return {"schema_version":2,"results":results,"verified":sum(x["disposition"]=="verified_candidate" for x in results),
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
