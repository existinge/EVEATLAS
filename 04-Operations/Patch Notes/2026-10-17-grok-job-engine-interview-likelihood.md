# Patch note — 2026-10-17 — Grok Job Engine Bot interview likelihood

**Branch:** `feat/grok-job-engine-interview-likelihood`  
**Scope:** Job Engine specification / agent handoff (not deployed)  
**Canonical change:** `01-Projects/Grok Job Engine - Interview Likelihood.md`

## Macro
Adds an independent, evidence-backed interview competitiveness parameter while preserving the Hopecore-first mission, daily US-remote discovery, and approval-gated applications.

## Micro
- Defines weighted six-factor 0–100 interview scoring and evidence-confidence handling.
- Separates interest, qualifications, interview competitiveness, and action priority.
- Requires original job URL, verification date, eligibility check, provenance, and actionable fit-gap guidance.
- Includes missing-data/null handling, dream-role stretch protections, QA acceptance tests and observed-outcome calibration guidelines.
- Names the **Grok Job Engine Bot** as the implementation owner.

## Scholar / Atlas awareness
Scholar should ingest this **architecture-level** change into its macro system map: the Job Engine now specifies an interview-likelihood decision feature with evidence and reviewer requirements. Do not count it as deployed runtime functionality. The Grok bot/operator must implement and test its prompts, storage, and daily reports separately.

## Validation
Specification review only; **no runtime bot tests performed**, no scheduler configured, no job applications sent.

## Next handoff
Grok Job Engine Bot implementer: integrate rubric into its actual score pipeline and tracker, test the nine acceptance cases, reconcile with live deployment, then return a dated handoff with proof and unresolved issues. Human approval remains required for sending or submitting.
