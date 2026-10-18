# Grok Job Engine Bot — Interview Likelihood v1

Status: **proposed specification; not yet wired into a running Grok bot**  
Owner: Grok Job Engine Bot (job discovery and application ranking)  
Updated: 2026-10-17  
Branch: `feat/grok-job-engine-interview-likelihood`

## Objective
Add an evidence-backed **Interview Likelihood** parameter to the Grok Job Engine Bot. The engine's north star remains **Hopecore**: enjoyable, meaningful opportunities intersecting creative AI, games/player platforms (including Valve/Deadlock), Asian/fandom media, BL/queer streaming tech, creator tools, language/culture, and adjacent content/platform operations. Don't replace this with a generic IT jobs board. Search daily and generate an actionable application queue; prioritize new, verified US-remote openings and the user's chosen interests. Default compensation floor: $22/hr except explicit high-Hopecore exceptions. Use Desperation Search Mode only by explicit user request.

## Separate scores (never conflate)
- `hopecore_fit` (0–100): intrinsic interest / ecosystem alignment.
- `qualification_fit` (0–100): demonstrable ability to perform the work.
- `interview_likelihood` (0–100 or null): **heuristic relative chance of securing an initial interview, NOT a calibrated percentage probability**.
- `interview_confidence` (`low`|`medium`|`high`): quality of evidence behind that estimate.
- `application_priority` (`apply_now`|`stretch_apply`|`network_first`|`research`|`skip`): final action decision; not merely a sorted score.
- `interview_factors`: an auditable, short breakdown of factors, evidence URLs and unknowns.
- `estimated_effort_minutes`: rough preparation/application effort, labeled estimate.

## Interview Likelihood — rubric
Each component has a 0–5 *observed fit* grade; use `null` where unverified. Compute a weighted score only when at least 60 of 100 possible weight points have evidence; otherwise set `interview_likelihood: null` and `interview_confidence: low` (display “Insufficient evidence,” not zero). For known components, weighted score = round(100 × sum(weight × grade/5) / sum(known weights)). Never infer missing components as the midpoint or a zero.

| Component | Weight | Evidence |
|---|---:|---|
| Core requirements match | 30 | Specific mandatory and preferred criteria versus CV and verifiable history |
| Relevant accomplishments | 20 | Concrete support/technical/QA/ops outcomes and transferable work |
| Seniority and scope alignment | 15 | Years, ownership, team scale, professional level |
| Application competitiveness | 15 | Genuine referral or recruiter contact, portfolio/proof, tailored narrative; never infer a referral |
| Hiring practicality | 10 | Verified US-remote eligibility, compensation compatibility, employment constraints |
| Posting freshness / hiring signals | 10 | Original ATS posting, date if verifiable, active status, verified recruiter engagement |

If hard location/work authorization/licensing requirements are **known** not to be met, mark `eligibility: ineligible` and `application_priority: skip`, regardless of numeric score. If a hard requirement is unclear, mark `eligibility: unverified`; do not represent the application as certain to qualify. Prefer original ATS URLs; stale, expired, duplicate, or closed jobs should be skipped until reverified. Avoid treating applicant counts, “100+ applicants”, ATS folklore or prestige as measured probabilities.

Confidence:
- **high**: original active posting + sufficiently detailed criteria + up-to-date resume evidence + 5+ component grades.
- **medium**: original posting + resume evidence + at least 3 graded components.
- **low**: otherwise, or if significant requirements are unknown. Degrade confidence when freshness cannot be verified.

## Priority logic — Hopecore comes first
1. Verify the role is open and plausibly eligible; deduplicate by ATS ID / canonical URL and company-title-location aliases.
2. Assess Hopecore first. Do **not** bury a Hopecore dream role just because Interview Likelihood is lower.
3. Cross-classify:
   - High Hopecore + high interview score (>=70): `apply_now`, highest priority.
   - High Hopecore + medium (40–69): `apply_now` or `network_first`, depending on fit gaps and contact channel.
   - High Hopecore + low (<40): `stretch_apply` if eligible; include one credible path to increase odds.
   - Strong interview + low Hopecore: backup only, never dominate the default daily queue.
   - Low-confidence/null likelihood: `research` while retaining high-Hopecore options in a visible “needs verification” lane.
4. Factor in urgency, deadline, salary, effort, and network leverage as tie-breakers. Never silently discard a role solely due to a heuristic estimate.

## Mandatory output for every shortlisted role
```json
{
  "company": "",
  "title": "",
  "original_posting_url": "",
  "verified_open_at": "YYYY-MM-DD or null",
  "remote_us_eligible": "yes|no|unverified",
  "hopecore_fit": 0,
  "qualification_fit": 0,
  "interview_likelihood": null,
  "interview_confidence": "low",
  "interview_factors": [
    {"factor": "core_requirements", "weight": 30, "grade_0_to_5": null, "evidence": "", "unknowns": ""}
  ],
  "eligibility": "eligible|ineligible|unverified",
  "application_priority": "research",
  "next_action": "",
  "estimated_effort_minutes": null
}
```
Output a concise human-readable **Why interview?** justification: 2 strongest signals, top missing requirement, and one concrete improvement (resume wording, tailored evidence, networking outreach, or targeted project). Use `null` rather than fake precision. Keep source URLs and check date. Never confuse `interview_likelihood: 78` with a measured 78% chance.

## Daily engine execution
- Discover verified roles across *all* Hopecore lanes before broad IT fallbacks. Favor employer ATS pages. Track evaluated, shortlisted, applied, contacted, replied, interviewed, rejected and closed independently.
- Produce daily recommended application actions, with immediate high-Hopecore/high-competitiveness opportunities first and a distinct stretch lane. Maintain an outreach lane for beloved companies without an active posting, clearly tagged as cold outreach.
- Personalize resumes and draft emails based on actual credentials. Have a separate critical reviewer grade application artifacts and identify concrete factual weaknesses; no automatic agreement. Reconcile changes into a clear handoff.
- Any email sending, submission, public outreach or other external action requires explicit approval under `AGENTS.md`. Do not claim applications were submitted because they were drafted.
- Track `application_date`, `interview_invite`, `source`, `score_at_application`, and score version for **future** calibration. Report observed interview rates only after enough actual labeled outcomes and separate them from heuristics. Do not train on sensitive personal traits or infer protected traits.

## Acceptance tests (to be executed by implementation bot)
1. Dream role at 90 Hopecore / 35 likelihood stays visible as `stretch_apply`; never silently discarded.
2. Generic IT role at 30 Hopecore / 85 likelihood remains backup, not primary.
3. Open ATS job with good CV match gets traceable factor evidence and separate scores.
4. Missing applicant competition or posting date doesn't become invented numbers.
5. 2/6 verified factors totaling <60 weight yields likelihood null and low confidence.
6. Closed role, duplicate role, and demonstrably ineligible location are blocked or flagged.
7. Output includes meaningful next action, provenance and verification date.
8. No send/submit occurs without approval.
9. Changing scoring rules triggers a score-version bump and dated patch note.

## Grok bot implementation handoff
Grok Job Engine Bot must adopt this schema and rubric in discovery, scoring, daily reports, tracker storage, and reviewer prompts. Preserve Hopecore as the leading objective. This repository note alone **does not** prove that the running Grok bot has consumed the rule or its scheduler was changed. Report implementation, tests and deployment separately.
