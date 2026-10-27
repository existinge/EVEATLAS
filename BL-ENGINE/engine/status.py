"""Append-only feedback events; no guessing between statuses."""
VALID={"completed","watching","dropped","no_skip","maybe","not_tonight","plan","unknown"}
BLOCK={"completed","watching","dropped","no_skip","plan"}
def current_status(events, production_id):
    relevant=[e for e in events if e["production_id"]==production_id]
    if not relevant:return "unknown"
    relevant.sort(key=lambda e:(e["timestamp"],e.get("sequence",0)))
    status=relevant[-1]["status"]
    if status not in VALID:raise ValueError("Unsupported status")
    return status

def eligible_as_new(status):
    return status=="unknown"

def append_feedback(events, event):
    if event["status"] not in VALID:raise ValueError("Unsupported status")
    if not event.get("source"):raise ValueError("Feedback provenance required")
    if not event.get("timestamp"):raise ValueError("Timestamp required")
    return [*events,dict(event)]
