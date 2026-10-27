"""BL Engine v3 CLI. Private workbook and candidate JSON stay outside the repo."""
import argparse
import json
from pathlib import Path
from .workbook import import_canonical
from .ranking import triage

def run(workbook,candidates,output):
    canonical=import_canonical(workbook)
    incoming=json.loads(Path(candidates).read_text(encoding="utf-8"))
    if not isinstance(incoming,list):raise ValueError("Candidate JSON must be an array")
    result=triage(incoming,canonical["records"],canonical["events"])
    payload={"results":result,"canonical_diagnostics":canonical["diagnostics"],
             "summary":{k:len(v) for k,v in result.items()}}
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    return payload

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",required=True,help="Private canonical XLSX")
    p.add_argument("--candidates",required=True,help="Array of candidate JSON objects")
    p.add_argument("--output",required=True,help="JSON report destination")
    args=p.parse_args()
    summary=run(args.workbook,args.candidates,args.output)["summary"]
    print(json.dumps(summary))

if __name__=="__main__":main()
