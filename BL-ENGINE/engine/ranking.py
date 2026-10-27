"""Preserve unknown discoveries even when taste evaluation is weak."""
from .identity import resolve
from .status import current_status
from .evidence import evidence_gate
from .scoring import score

def triage(candidates, known, events):
    approved,discovery,excluded=[],[],[]
    for candidate in candidates:
        match=resolve(candidate.get("title"),known,country=candidate.get("country"),year=candidate.get("year"))
        if match["state"]!="unresolved":
            excluded.append({"title":candidate.get("title"),"reason":"identity_"+match["state"],"match":match})
            continue
        # Cannot prove novelty from a negative title search: retain unknown in discovery feed.
        item=dict(candidate)
        item["identity_state"]="unresolved"
        item["fit_score"]=score(candidate.get("criteria",{}))
        item["gate"]=evidence_gate(candidate)
        if item["gate"]["approved"] and candidate.get("identity_verified_new") is True:
            approved.append(item)
        else:
            discovery.append(item)
    approved.sort(key=lambda c:c["fit_score"] if c["fit_score"] is not None else -1,reverse=True)
    discovery.sort(key=lambda c:c["fit_score"] if c["fit_score"] is not None else -1,reverse=True)
    return {"recommendations":approved,"unknown_discoveries":discovery,"excluded":excluded}
