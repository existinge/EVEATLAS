"""Production identity matching with explicit aliases and conservative fuzzy quarantine."""
from difflib import SequenceMatcher
import unicodedata

def normalize(title):
    value=unicodedata.normalize("NFKC",title or "").casefold()
    return "".join(c for c in value if c.isalnum())

def resolve(title,records,*,country=None,year=None):
    key=normalize(title)
    if not key:return {"state":"uncertain","id":None,"matches":[]}
    exact=[]
    for record in records:
        if key in {normalize(n) for n in [record.get("title","")]+record.get("aliases",[])}:
            exact.append(record)
    # Never discard an exact match merely because sparse or contradictory metadata differs.
    if len(exact)==1:return {"state":"matched","id":exact[0]["id"],"matches":[exact[0]["id"]]}
    if len(exact)>1:return {"state":"ambiguous","id":None,"matches":[r["id"] for r in exact]}
    near=[]
    for record in records:
        names=[record.get("title","")]+record.get("aliases",[])
        if any(len(key)>=6 and len(normalize(n))>=6 and SequenceMatcher(None,key,normalize(n)).ratio()>=0.88 for n in names):
            near.append(record["id"])
    if near:return {"state":"ambiguous","id":None,"matches":near}
    return {"state":"unresolved","id":None,"matches":[]}
