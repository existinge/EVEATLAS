# Treasurer — Deterministic Micro-Accounting Skill

Treasurer is primarily code, not a continuously running LLM.

### Every paid-model worker handoff
1. Check the objective budget using `atlas_treasurer.snapshot`.
2. Reserve worst-case estimated spend with a stable idempotency key.
3. Execute only via an authorized worker adapter. A failed call that may have reached the provider must stay uncertain.
4. Reconcile usage using provider or trusted gateway metering; never bill zero by assumption.
5. Emit structured warnings or critical incidents. Pause paid dispatch if allowance is gone or uncertain liabilities make continuation unsafe.
6. Send important alerts to the coordinator; give Codex the incident and cost history at final review.
7. Produce sanitized receipt summaries for vault documentation when appropriate.

### Never
- Raise a spending limit automatically.
- Mark unknown charges as free.
- Trust an unverified worker's self-reported invoice.
- Commit private ledger or financial/account data to a public repo.
- Execute an external financial action.

See [[04-Operations/ATLAS Treasurer]].
