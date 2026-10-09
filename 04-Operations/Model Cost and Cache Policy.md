# Model Cost and Cache Policy

1. Deterministic local tools first, narrow retrieval second, cheap competent model third, premium reasoning only when complexity warrants.
2. Reuse stable context prefixes where supported; retrieve only relevant canonical notes, not the whole vault.
3. Verify cache capabilities, TTLs, minimum sizes, read/write pricing and usage counters **per provider and model**.
4. Log estimated and actual input/output token spending, cached tokens, retries and quality outcomes. Fail closed on exceeded budget.
5. Require explicit human approval before paid API integrations or provider changes. Do not claim cost savings before observing them.
6. Never cache private credentials or customer data into public or shared contexts.

Caching is a deployment objective, **not yet verified active**.