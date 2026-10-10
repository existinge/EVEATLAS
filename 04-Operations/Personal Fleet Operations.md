# ATLAS Personal Fleet — Operating Priorities

## Mission
Build an operational AI workforce to reduce manual supervision across business building. EVEATLAS remains the canonical planning/evidence repository; cloud services execute persistent jobs. EveClaw/OpenClaw is the optional PC-resident administrative client, never a required execution host.

## Ordered operational lanes
1. **Website Watch + Maintenance** — availability, broken links, technical issues, optional change proposals, tests, Codex independent final review, human approval for production deployment.
2. **Credits + Services Research** — recurring eligibility verification for student/startup programs, cloud/model service comparison, deadline and application tracking; draft but do not submit, register or spend without approval.
3. **Development Loop** — bounded plan, implement, test, repair, Codex final review, artifact receipt. Costs and provider limits enforce stopping rules.
4. **Fleet Operations** — provider and job health, queued work, budget visibility, human approvals and exceptional incidents.

## Immediate first operational automation
`tools/website_watch.py` and `.github/workflows/website-watch.yml` provide read-only HTTPS health checking and GitHub Actions failure status and archived run receipt. This is a limited real automation, not autonomous website repair. The scheduled workflow runs only after it reaches the repository default branch and GitHub Actions are enabled. It is not running merely because a PR contains the file.

## Implementation gates
- No always-on dependency on the operator's personal PC.
- Cloud control plane + durable state; GitHub Actions for small periodic checks, task queue/managed compute for long jobs.
- Do not use a GitHub Actions scheduled job to pretend to run indefinitely; CI timeouts and scheduling delays apply.
- DeepSeek/Gemini/Codex worker adapters must be real authenticated invocations with receipts and accounting before describing loops as autonomous.
- Codex review is mandatory before engineering completion. Codex unavailable => AWAITING_FINAL_REVIEW; no silent fallback.
- Public repo: no API keys, private application details, personal financial data, student identity documents or sensitive records.
- External email, submitting applications, deploying websites, paid service activation and purchases require specific approval.
- Prefer one tested loop to ten unconnected prompt-only agents.

## Minimum operating dashboard
Active objectives, latest healthy check, credit/grant opportunities awaiting review, jobs waiting for Codex, approvals needed, weekly API usage, and blocked reasons.

## First 2 measurable milestones
- Website check scheduled in cloud, failure marks the workflow failed and produces a receipt, healthy run does not create an issue.
- Credits scout generates a verified weekly opportunity brief with official eligibility citations, original dates and application-ready drafts, without applying automatically.

## Next integration
Provision affordable hosted state/queue, secure provider credentials, implement one real coding worker, an independent read-only Codex final review adapter, and a bounded failure-to-repair-to-review scenario. No unsupported model identifiers or claimed credits.
