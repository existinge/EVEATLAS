#!/usr/bin/env python3
"""Deterministic opportunity score helper. Unknown evidence is NOT treated as zero."""
import argparse,json,sys
from pathlib import Path
POS={"pain":3,"frequency":2,"buyers":3,"payment_evidence":4,"solution_gap":2,"feasibility":2,"distribution":2,"differentiation":2}
NEG={"regulatory_risk":3,"support_burden":2}
def score(o):
 unknown=[k for k in (*POS,*NEG) if o.get(k) is None]
 for k in (*POS,*NEG):
  v=o.get(k)
  if v is not None and (type(v) not in (int,float) or not 0<=v<=5): raise ValueError(f'{k}: expected 0..5 or null')
 subtotal=sum(o[k]*w for k,w in POS.items() if o.get(k) is not None)-sum(o[k]*w for k,w in NEG.items() if o.get(k) is not None)
 return {'id':o.get('id'),'partial_score':subtotal,'unknown':unknown,'complete':not unknown}
def main():
 pa=argparse.ArgumentParser();pa.add_argument('action',choices=['score']);pa.add_argument('file',type=Path);args=pa.parse_args()
 for o in json.loads(args.file.read_text()):print(json.dumps(score(o),sort_keys=True))
if __name__=='__main__':main()
