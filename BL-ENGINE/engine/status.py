"""Explicit watch history with normalized states and provenance. Never infer watched from skipped."""
VALID={"completed","watching","dropped","no_skip","maybe","not_tonight","plan","unknown"}
def normalize_status(raw):
    value=(raw or "").strip().casefold().replace("_"," ")
    if value.startswith("completed") or value in ("seen","watched","finished"):return "completed"
    if value.startswith(("watching","caught up")):return "watching"
    if value.startswith(("dropped","paused")):return "dropped"
    if value.startswith(("no / skip","no/skip","do not recommend","skip","not interested")):return "no_skip"
    if value.startswith(("plan","waiting")):return "plan"
    if value.startswith(("not tonight","not now")):return "not_tonight"
    if value.startswith(("maybe","verify","undecided")):return "maybe"
    return "unknown"

def current_status(events,production_id):
    relevant=[e for e in events if e["production_id"]==production_id]
    if not relevant:return "unknown"
    relevant.sort(key=lambda e:(e["timestamp"],e.get("sequence",0)))
    return normalize_status(relevant[-1]["status"])

def eligible_as_new(status):
    return normalize_status(status)=="unknown"

def append_feedback(events,event):
    if normalize_status(event.get("status"))=="unknown":
        raise ValueError("Unsupported or unknown feedback status")
    if not event.get("source"):raise ValueError("Feedback provenance required")
    if not event.get("timestamp"):raise ValueError("Timestamp required")
    return [*events,dict(event)]
