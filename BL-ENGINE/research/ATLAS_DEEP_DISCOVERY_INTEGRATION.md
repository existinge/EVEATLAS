# ATLAS Deep Discovery — integration (v3: discovery-first, access-neutral)

Branch: `feat/atlas-deep-discovery-gates` based on `feat/bl-engine-v3-gates`.

This is an **offline evidence gate**, not an autonomous researcher. It consumes
candidate research receipts and canonical tracker exclusions. It does not use
paid APIs, secrets, web search, or modify the user's private tracker.

Run:
```sh
python -m unittest discover -s tests -p 'test_deep_discovery.py' -v
python tools/deep_discovery.py path/to/private-research-input.json --output review.json
```

Input: `known_titles: [{title,aliases,status}]` and `candidates` with
`title,aliases,released,central_mm_romance,healthy_consent,
romantic_payoff,stream:{official_url,region_verified,english_subtitles_verified},
sources:[URLs]`.

`discovery_profile` is `broad_bl` (the default) or
`feminine_misidentification`. Set it on the payload for a lane, or on a
candidate to override that lane. An unknown profile blocks admission.
The broad profile does not require a feminine-presentation or mistaken-gender
trope. The specialist profile additionally requires
`actual_gender_confusion: true` OR `feminine_presenting_male: true`, and a
nonempty `trope_evidence: [HTTPS URLs]` list. These fields describe a male
character; they must not be used to misclassify a trans woman as a male lead.

Only literal JSON `true` counts as a supported factual claim. Strings and
numbers do not prove anything. Source URLs require HTTPS with a hostname;
the gate cannot independently verify their contents. It does not retrieve
URLs, watch scenes, or authenticate claims about identity, payoff or consent.

### Discovery-first classification (2026-11-02 user policy)
- **blocked:** already tracked under any status or alias, empty title, explicit
  hard reject, or unsupported discovery profile. Never call an existing backlog
  item a new discovery.
- **research_lead:** apparently new identity but one or more story facts,
  completion, romance, niche evidence or source receipts remain unverified.
  Retain this title and its research gaps in the discoverable pool. A lead is
  not yet a recommendation.
- **verified_candidate:** all required *story receipt fields* present. The
  label is a receipt-quality result, not an independent truth certification.

**US playback, availability region, English subtitles, and even an official
playback URL are optional metadata, NEVER admission criteria.** The viewer has
access to VPNs and alternate viewing sources. Record an official link when
known and any limitations in `access.warnings`; do not invent unofficial
links or bypass claims. Do not label the video playable in a region unless
tested. Prioritize uncovering real Asian M/M titles, tracking original-language
aliases and verifying story/romance. Preserve lesser-known, archival, indie,
regional, films and short-form discoveries even when stream status is unknown.

`run()` adds counts `research_leads`, `excluded` and `discovered`.
`verified` counts only story receipt-complete novel candidates. The previous
R02 run's zero-admission result was partly due to an inappropriate streaming
gate; do not reinterpret the new research-lead count as independently validated
titles.

Gates are fail-closed. Unknown = blocked. Aliases unify by Unicode alphanumeric
normalization. Every supplied tracked identity blocks fresh admission,
including unknown, blank, manual, and alias statuses. Classify backlog versus
excluded outside this gate and preserve original status provenance. Distinct live-action adaptations should have separate
canonical titles and only their actual aliases attached. Do not use bare
`Love Stage` across adaptations.

Before using this in a real multi-agent run, implement: import adapter for
private R43 XLSX; independent evidence review with dated source
verification and optional access metadata; a multi-language research coverage log; deterministic persistent
feedback writeback; a real DeepSeek worker tool runner; and runtime receipts.
A tool call returning no candidates is valid. Never call this an ATLAS agent
run without execution receipts.
