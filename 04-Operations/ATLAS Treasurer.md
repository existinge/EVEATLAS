# ATLAS Treasurer — Accounting and Critical-State Control

**State:** Implemented deterministic, local SQLite foundation. **Not** connected to provider invoices, API metering or live model workers.

## Purpose
Prevent a multi-agent fleet from spending without preflight reservations, keep detailed mutable financial telemetry out of the public repo, and send structured cost incidents to the coordinator and eventually Codex.

## Rules
- Worker agents report usage to Treasurer. Workers never write ledger truth directly to GitHub.
- Paid dispatch requires an atomic max-cost reservation. Missing price ceilings means block the dispatch, not assume zero.
- Provider/gateway usage reports can reconcile the reservation. Unverified estimates are never described as actual invoices.
- Unknown whether a provider charged? Mark `uncertain` and retain reserved funds until reconciliation.
- Overruns produce critical incidents. Accounting controls act deterministically without waiting for Codex.
- Codex receives relevant critical financial context and remains mandatory final technical reviewer, but cannot automatically increase budget or waive permission gates.
- All detailed records reside under `private/` and remain gitignored; sanitized aggregates may be voluntarily promoted to canonical research/operations notes.
- Monetary values are rounded upward to cents. For sub-cent billing or large-volume usage, use a finer-grained production ledger before enabling live dispatch.

## Python usage
Create a run:
```bash
python tools/atlas_loop.py start examples/atlas-loop-plan.json --budget 2
```
Run accounting commands using the same default database or pass `--db <path>` before the subcommand:
```bash
python tools/atlas_loop.py budget RUN_ID
python tools/atlas_loop.py reserve RUN_ID TASK_ID PROVIDER MODEL 0.25 --id billing-event-001
python tools/atlas_loop.py settle billing-event-001 0.17 --source provider_reported
python tools/atlas_loop.py uncertain billing-event-001 "provider request timed out after submission"
```

## Critical limitations and next integration
1. No remote/cloud accounting backend or fleet-wide locking across independent databases.
2. No authenticated providers wired into `atlas_loop.execute`; real billable calls must NOT be launched outside the Treasurer preflight path.
3. No automated provider cost reconciliation; manual CLI or trusted gateway must supply verified usage.
4. `review` CLI currently accepts an unauthenticated claim of Codex review; this is not a validated Codex execution receipt.
5. Atomic reservations prevent concurrent local SQLite clients from oversubscribing a run, but worker execution is not crash-reconciled yet.
6. Configure conservative upper bounds, shared cloud DB, invoice reconciliation and credential-scoped authenticated adapter calls before autonomous paid dispatch.

## Validation
`python -m unittest discover -s tests -v` runs reservations, idempotency, overrun and unknown-cost tests.
