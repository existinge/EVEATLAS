# T05 — Reasoning planner, branch horizon and visual recipes

Timebox: 30–45 minutes. Status: NOT STARTED. Depends on: T04/P4 (or explicitly scoped stub fallback).

## Build
Implement LLM planner adapter that reads confirmed conversational evidence plus decider frontier-interest events. Emit versioned semantic graph/visual recipe candidates with relationship provenance and action policy. Validate and commit newest plans atomically, bounded frontier (provisional breadth 3, depth 2), TTL and priorities; avoid combinatorial expansion.

Simulate planner delay and sudden user topic switch to ensure no screen freeze. Provide a fallback neutral display while new branch is unavailable. A novel concept cannot be silently labelled as an older concept.

## Gate P5
Planner extends likely next concepts without blocking decider; unanticipated exit triggers NEEDS_PLAN and a safe transition; same semantic graph can support multiple language surface forms; late plan is discarded under new epoch. Capture planner input, exact output and validation results without private data.

## Forbidden
Pre-writing all lesson content, guaranteeing perfect topic prediction, overriding newer human correction, asking planner to render every frame.

## Stop
Summarize branch hit rate from traces, planner calls/cost, stale-plan discards; then T06.
