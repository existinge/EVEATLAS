# BL Engine v3 — Canonical workbook integration

BL Engine v3 is a **deterministic audit and triage engine**, not a live streaming/web-search service. Its JSON outputs are suitable for a separate research orchestrator.

## Critical two-feed policy
- **Recommended Tonight:** independently identity-reviewed candidate, completed release, real BL romance, on-screen progression and an attributable official viewing source. Taste ranking applies here.
- **Unknown Discoveries:** **all** titles not conclusively matched to known productions, irrespective of taste score, even when sources or fit are weak. They retain reasons and identity confidence. Never fabricate approval.
- **Known Title Exclusions:** matches against canonical titles and aliases; blocked even when the recorded status is Maybe, Plan, Watched or Skip because they are not *new discoveries*. Existing backlog can be viewed separately.
- **Ambiguous identities** go to Unknown Discoveries but are explicitly marked ambiguous, never approved.

## Run

Requires Python 3.11+; no third-party packages needed.

```bash
python -m unittest discover -s BL-ENGINE/tests -v
PYTHONPATH=BL-ENGINE python -m engine.cli \
  --workbook "/private/BL_ENGINE_CANONICAL_v2026.10.26-r2.xlsx" \
  --candidates "/private/search-results.json" \
  --output "/private/bl-report.json"
```

`search-results.json` is an **array** of records. An eligible source-backed candidate looks like:

```json
[{
  "title": "Example series", "country": "Japan", "year": 2025,
  "identity_verified_new": true,
  "criteria": {
    "romance_payoff": 8, "acting_chemistry": 8, "plot_stakes": 7,
    "pursuit": 8, "visual_fit": 7, "pacing": 7
  },
  "evidence": {
    "completed": {"supported": true, "sources": ["https://example.org/official-finale"]},
    "real_bl": {"supported": true, "sources": ["https://example.org/official-synopsis"]},
    "romance_progression": {"supported": true, "sources": ["https://example.org/review"]},
    "official_stream": {"supported": true, "sources": ["https://example.org/distributor"]}
  }
}]
```

The URLs above are **schema examples only**, not actual BL sources. When generating real candidate data, require genuine links. `identity_verified_new` is a human/reviewer approval assertion; the gate cannot independently guarantee absence in an unseen private history.

## Data safety

The private canonical workbook stays outside public EVEATLAS. The loader parses the XML parts of XLSX using Python stdlib; it doesn't execute imported spreadsheet formulas. Reads: `WATCH`, `Alias Map`, `Viewing Reconciliation 2026`, `Oct 2026 Overrides`, plus read-only access to manual/rejection sheet parts. Only uniquely matched overrides are applied. Ambiguous and unmatched overrides are returned in diagnostics, not discarded without a trace.

## Research telemetry

`engine.search_history.log_search(path,query=...,source=...,language=...,candidates=...,eligible=...)` appends JSONL search audits to a private path. This currently requires the research caller to invoke it.

## Boundaries

The engine **does not itself conduct online research**, watch episodes, substantiate review claims, confirm live US streaming access, or launch independent agents. Those require external research workers and evidence collection. It is not yet a live autonomous BL search agent. No untested claims about actual taste predictions.

The GitHub PR is a draft pending test execution and review. Preserve the canonical workbook as read-only.
