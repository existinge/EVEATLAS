"""ATLAS Brain: deterministic routing and critical-state advice, no AI provider calls."""
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Worker:
    name: str
    capabilities: frozenset
    available: bool
    max_task_cents: int
    priority: int = 100

def choose_worker(required: Iterable[str], workers: Iterable[Worker], available_cents: int, critical_incidents=()):
    """Result is a bounded route recommendation, never permission to execute."""
    if available_cents < 0:
        raise ValueError("invalid available budget")
    if any(x.get("severity")=="critical" for x in critical_incidents):
        return {"action":"hold","reason":"critical_state","worker":None}
    need=frozenset(required)
    eligible=[w for w in workers if w.available and need.issubset(w.capabilities)
              and 0 <= w.max_task_cents <= available_cents]
    if not eligible:
        return {"action":"escalate","reason":"no_available_budgeted_worker","worker":None}
    winner=min(eligible,key=lambda w:(w.priority,w.max_task_cents,w.name))
    return {"action":"route","worker":winner.name,"max_task_cents":winner.max_task_cents,
            "reason":"capability_and_budget_match"}

def retry_advice(attempts, max_attempts, signatures, critical_incidents=()):
    if any(x.get("severity")=="critical" for x in critical_incidents):
        return {"action":"stop","reason":"critical_incident"}
    if attempts>=max_attempts:
        return {"action":"escalate","reason":"retry_cap"}
    if len(signatures)>=2 and signatures[-1]==signatures[-2]:
        return {"action":"switch_strategy","reason":"repeated_identical_failure"}
    return {"action":"retry","reason":"bounded_recovery"}
