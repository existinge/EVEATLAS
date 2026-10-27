"""Two-feed discovery triage: unknown never disappears due to poor taste fit."""
from .identity import resolve
from .status import current_status
from .evidence import evidence_gate
from .scoring import score

BLOCKED_PREFIXES=("completed","watching","dropped","no / skip","no_skip","do not recommend","plan","waiting")
def _blocked(status):
    return (status or "").casefold().strip().startswith(BLOCKED_PREFIXES)

def triage(candidates, known, events):
    recommendations,unknown_discoveries,excluded=[],[],[]
    # exact and alias matches always get checked against user status.
    for candidate in candidates:
        title=candidate.get("title","")
        match=resolve(title,known,country=candidate.get("country"),year=candidate.get("year"))
        if match["state"]=="matched":
            status=current_status(events,match["id"])
            excluded.append({"title":title,"reason":"known_title","status":status,"match":match})
            continue
        if match["state"]=="ambiguous":
            unknown_discoveries.append({**candidate,"identity_state":"ambiguous","fit_score":score(candidate.get("criteria",{})),
                "gate":{"approved":False,"reasons":["ambiguous_identity"]}})
            continue
        item=dict(candidate)
        item["identity_state"]="unresolved"
        item["fit_score"]=score(candidate.get("criteria",{}))
        item["gate"]=evidence_gate(candidate)
        # Only explicit external identity review can approve otherwise unresolved names.
        if item["gate"]["approved"] and candidate.get("identity_verified_new") is True:
            recommendations.append(item)
        else:
            unknown_discoveries.append(item)
    sortkey=lambda c:c["fit_score"] if c.get("fit_score") is not None else -1
    recommendations.sort(key=sortkey,reverse=True)
    unknown_discoveries.sort(key=sortkey,reverse=True)
    return {"recommendations":recommendations,"unknown_discoveries":unknown_discoveries,"excluded":excluded}
