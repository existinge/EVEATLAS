# Agent execution ticket index — one at a time

Read [[../START_HERE]] and repository-root AGENTS.md before any ticket.
Current state: T00 complete, P0 acceptance pending. Dispatch T01 only after review. See [NEXT_ACTION.md](../NEXT_ACTION.md).

| Ticket | Output | Gate | Rule |
|---|---|---|---|
| [[T00-PREFLIGHT]] | Environment + API evidence | P0 | Do not code beyond tiny smoke check |
| [[T01-SHARED-SPACE]] | Reducer + event log + replay | P1 | No models or graphics libraries required |
| [[T02-COORDINATOR]] | Deterministic proposal validator | P2 | No model judge |
| [[T03-CANVAS]] | Persistent tldraw objects / updates | P3 | No full-scene redraw each turn |
| [[T04-DECIDER]] | Stub plus real candidate adapter | P4 | No provider-specific coupling |
| [[T05-PLANNER]] | Branching horizon and recipes | P5 | No blocking the fast loop |
| [[T06-DUPLEX]] | Live voice adapter and capability report | P6 | No unsupported realtime claims |
| [[T07-INTEGRATION]] | Multilingual real-session evaluation | P7 | No cherry-picked demo |

## Operating discipline
Use one active ticket. Before implementation, record current branch, build commands, existing tests and expected files. Each ticket produces runnable evidence and handoff (see ../ATLAS_HANDOFF.md). If blocked, stop and state exact failure and next action; do not solve by silently changing the product vision. A test that passes with injected scripted events must be identified as SIMULATED, not a full end-to-end voice result.

## Temporary stub rule
Stubs must share the same versioned protocol and be deliberately replaced later; no throwaway scaffold architecture. T01–T03 run without model frameworks, credentials or inference. Each ticket stops at its own gate.
