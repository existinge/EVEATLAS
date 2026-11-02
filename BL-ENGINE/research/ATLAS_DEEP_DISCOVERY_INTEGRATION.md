# ATLAS Deep Discovery — integration (v2)

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

All required flags accept literal JSON `true` only. Strings and numbers do not
prove a claim. URLs require HTTPS and a hostname. This validates syntax only:
the gate does not retrieve URLs, verify identity or assert that a synopsis
proves an ending or consent. `region_verified` must remain false unless actual
authorized region playback was tested. A catalog listing alone cannot pass
that requirement. The result's `verified_candidate` label means the supplied
receipt passed these checks, not independent source authentication.

Gates are fail-closed. Unknown = blocked. Aliases unify by Unicode alphanumeric
normalization. Every supplied tracked identity blocks fresh admission,
including unknown, blank, manual, and alias statuses. Classify backlog versus
excluded outside this gate and preserve original status provenance. Distinct live-action adaptations should have separate
canonical titles and only their actual aliases attached. Do not use bare
`Love Stage` across adaptations.

Before using this in a real multi-agent run, implement: import adapter for
private R43 XLSX; independent evidence review with date/region/official source
verification; a multi-language research coverage log; deterministic persistent
feedback writeback; a real DeepSeek worker tool runner; and runtime receipts.
A tool call returning no candidates is valid. Never call this an ATLAS agent
run without execution receipts.
