# Signal Desk — Evidence and Research Operations

**State:** Local ingestion foundation. Not an autonomous web or X monitoring service.

## Research outputs
- An evidence JSON record with a claim, dated original source, source type, exact support and uncertainty.
- A reviewed brief containing up to three cleared findings.
- A JSON receipt reporting accepted, pending, covered and skipped records.
- SQLite ledger identifying covered events. Only reviewed findings included in a brief are covered.

## Local usage
```bash
python tools/signal_desk.py examples/signal-desk-candidates.json
python -m unittest discover -s tests -v
```
Default database: `private/signal-desk.sqlite3`. Default outputs: `private/signal-desk-runs/<run-id>/`. Both are excluded from Git. Use `--db` and `--output` to override.

## Extension plan (not yet implemented)
1. Add permissioned public RSS, documentation release-feed and GitHub release adapters; bounded requests, timeouts, attribution and caching.
2. Evaluate X access via Grok Bot manual handoff or an official API; never assume free programmatic access.
3. Add a configurable per-run source cap and model-call accounting for actual paid integrations.
4. Add scheduled execution only after source access, error handling, tests and notification behavior are verified.
5. Optional project-aware proposal writer, gated by the existing AGENTS.md contract.

## Failure semantics
Malformed batches fail without partially inserting records. Pending/blocked records never enter the public brief. Previously covered items are skipped unless a material update is declared with a reason. This is a local data-quality guarantee, not independent confirmation of a factual claim.

## Privacy
This is a **public repo**. Do not commit run outputs, internal scouting details, proprietary feeds or sensitive research evidence. The canonical vault contains the skill and method; private mutable state remains local.
