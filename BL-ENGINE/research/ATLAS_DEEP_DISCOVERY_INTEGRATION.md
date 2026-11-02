# ATLAS Deep Discovery — integration (v1)

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
`title,aliases,released,central_mm_romance,healthy_consent,actual_gender_confusion,
romantic_payoff,stream:{official_url,region_verified,english_subtitles_verified},
sources:[URLs]`.

Gates are fail-closed. Unknown = blocked. Aliases unify by Unicode alphanumeric
normalization, but distinct live-action adaptations should have separate
canonical titles and only their actual aliases attached. Do not use bare
`Love Stage` across adaptations.

Before using this in a real multi-agent run, implement: import adapter for
private R43 XLSX; independent evidence review with date/region/official source
verification; a multi-language research coverage log; deterministic persistent
feedback writeback; a real DeepSeek worker tool runner; and runtime receipts.
A tool call returning no candidates is valid. Never call this an ATLAS agent
run without execution receipts.
