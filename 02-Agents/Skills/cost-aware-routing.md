# Skill: cost-aware-routing

Classify work as retrieval, extraction, simple transformation, planning, complex engineering or independent audit. Prefer deterministic tooling for transformations, then cheaper appropriate models; escalate to premium reasoning for harder/debugging tasks.

Set token, retry and cost ceilings; log provider/model, usage, date, estimated spend, completion and quality. Check actual provider documentation, logging and billing for prompt caching. Stable reusable context can help but **does not mean caching has been enabled**.

Never silently change to a less private provider. Avoid loading the entire vault into each prompt.