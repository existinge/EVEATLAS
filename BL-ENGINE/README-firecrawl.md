# ATLAS × BL Engine: Firecrawl research adapter

This extends the v3 gates on `feat/bl-engine-v3-gates`; it does not replace BL Engine or publish private user records. The provider receives only public queries and URLs. The workbook, checkpoints, historical archives, reviews and receipts stay in private storage.

## Flow

1. `build_index` loads raw checkpoint WATCH/aliases/manual/explicit events/research logs, all identity-bearing workbook sheets, and the hash-checked R78 reconciled archive from the R79 audit. Optional earlier workbooks extend historical coverage. Formula keys are ignored; Unicode-normalized raw title keys are rebuilt. Exact/alias hits block freshness regardless of status. Historical references block freshness pending review, not proof of watch status. Fuzzy collisions are quarantined. Explicit later events override stale WATCH rows; duplicate Completed/Plan preserves completed evidence. Distinct releases are never merged merely by fuzzy similarity.
2. `FirecrawlProvider` implements search, map, bounded catalog crawl and structured extraction via injectable connector transport or Firecrawl v2 REST (`FIRECRAWL_API_KEY`). `live_batches` pulls a bounded plan in sequence, preserving receipts; only explicit catalog URLs are extracted before the identity gate. A map title parser can screen known detail-page identities without scraping them.
3. `run_round` screens every candidate before detailed research, then applies a title-only reviewer crosswalk (native title, aliases, release identity, source links). It repeats the identity check before evidence research and after newly discovered aliases. Unknown or fuzzy identities remain quarantined until reviewed. It continues to other batches when no candidate qualifies.
4. `public_evidence` retrieves structured public evidence. Reviewer assertions (not extraction alone) must verify identity, completion, mutual central romance, happy ending, cozy fit, non-coercive/non-erotic content, full runtime and official stream. The strict gate defaults to 80 minutes and new-relationship buildup; vertical, short, and explicit erotic productions never qualify. Existing v3 `evidence_gate` and `triage` remain the final scoring/approval path. Unverified leads and exclusion receipts remain separately available, without padding recommendations.

## CLI

```sh
PYTHONPATH=BL-ENGINE python -m engine.firecrawl_research \
  --checkpoint /private/latest.json --workbook /private/canonical.xlsx \
  --history-archive /private/R79-audit.zip --extra-workbook /private/older-audit.xlsx \
  --plan /private/public-plan.json --reviews /private/reviews.json \
  --replay /private/live-connector-receipts.json --output /private/report.json
```

Omit `--replay` to use the REST transport with an environment API key. This host's connector can execute public retrieval and then supply the actual response records for replay. `--replay` is not a new network call. Record each response as `{ "operation": "search|map|crawl|scrape", "selector": "query or URL", "response": {...} }`. The plan is an array of objects with `id`, `operation` and `query` or `url`; optional `limit`, `catalog_urls`, `include_paths`, and for map `candidate_path_prefix`, `title_pattern` (one capture group), `country`. `catalog` invokes structured title-only scrape. Reviews are keyed by normalized title under `identities` (aliases, identity_verified_new, identity_review_sources) and `evidence` (urls, reviewed fields). The reviewer must establish actual production identity and explicitly source each fact; never use synthetic facts or inferred ratings. The output records input hashes, candidate dispositions, source counts and provider receipts. A result with zero strict matches is valid.

```sh
python -m unittest discover -s BL-ENGINE/tests -v
```

## Boundaries

The adapter is additive on the feature branch; it is not a deployed plugin runtime. REST network behavior needs an authenticated environment integration test. No source extraction proves US video playback, and no recovered archive proves every prior title is present. The private history can contain conflicting statuses and same-title productions; conflicts are preserved, not silently flattened. Keep private reports outside the public repository. Do not commit API keys or user history. The prior v3 branch has diverged from main; review and reconcile before merging.
