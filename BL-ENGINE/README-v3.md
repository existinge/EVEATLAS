# BL Engine v3 — identity, evidence and two-lane discovery

The engine produces **two separate feeds**:
1. **Recommended tonight:** independently supported completion, genuine romance, relationship progression, official streaming evidence, confirmed novelty.
2. **Unknown discoveries:** *all* previously unresolved titles, including low-fit, under-verified or experimental content. Never suppress novelty because taste scoring is poor; mark confidence and reasons clearly.

Known titles, even if an alias is matched, belong in **excluded**, not either discovery feed. Identity uncertainty is never proof that a title is new. An explicit reviewer can set `identity_verified_new=true` only after independently checking against private canonical records.

## Usage
Run `python -m unittest discover -s BL-ENGINE/tests -v` from the repository root.

API:
- `engine.identity.resolve(title, records, country=...,year=...)`
- `engine.status.append_feedback(events,event)`, `current_status`
- `engine.evidence.evidence_gate(candidate)`
- `engine.scoring.score(criteria)`
- `engine.ranking.triage(candidates,known,events)`
- `engine.search_history.log_search(...)`

Private user workbook stays outside public GitHub. v3 currently supports JSON record inputs; automatic XLSX import, multilingual fuzzy candidate retrieval, historical migration, and provider adapters still require separate implementation. It does not run autonomous background agents or connect to streaming services. Never claim the full 26-tab workbook has been reprocessed by this code until a private import workflow has run.
