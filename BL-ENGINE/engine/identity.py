"""Conservative production identity resolution. Ambiguity is never novelty."""
import re
import unicodedata

def normalize(title):
    value=unicodedata.normalize("NFKC", title or "").casefold()
    return "".join(c for c in value if c.isalnum())

def resolve(title, records, *, country=None, year=None):
    """Return {state,id,matches}. No title string match is treated as guaranteed new."""
    key=normalize(title)
    if not key:
        return {"state":"uncertain","id":None,"matches":[]}
    matches=[]
    for record in records:
        names=[record.get("title","")]+record.get("aliases",[])
        if key in {normalize(n) for n in names}:
            matches.append(record)
    if country:
        matches=[m for m in matches if not m.get("country") or m["country"].casefold()==country.casefold()]
    if year:
        matches=[m for m in matches if not m.get("year") or int(m["year"])==int(year)]
    if len(matches)==1:
        return {"state":"matched","id":matches[0]["id"],"matches":[matches[0]["id"]]}
    if len(matches)>1:
        return {"state":"ambiguous","id":None,"matches":[m["id"] for m in matches]}
    return {"state":"unresolved","id":None,"matches":[]}
