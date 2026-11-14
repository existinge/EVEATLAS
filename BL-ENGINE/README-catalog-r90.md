# R90 catalog-first coverage worker

Extends the Firecrawl research adapter with bounded catalog plans, per-source coverage receipts, production-level deduplication and reviewed native-title crosswalks. Catalog rows are leads, not authoritative year/country/format claims. A crosswalk requires a reviewed source URL and evidence excerpt; unresolved or conflicting identities remain quarantined. A verified distinct sequel can bypass a parent-only fuzzy collision, but never an exact known identity or historical reference. Alternate edits are excluded. All previous history is indexed locally; provider calls contain only public sources and production titles.

Run from `BL-ENGINE`:

```sh
python -m unittest discover -s tests -v
python -m engine.catalog_coverage --checkpoint PRIVATE.json --workbook PRIVATE.xlsx \
  --history-archive PRIVATE_HISTORY.zip --extra-workbook PRIVATE_EARLIER.xlsx \
  --plan catalog-plan.json --crosswalk reviewed-crosswalk.json --reviews evidence-reviews.json \
  --replay connector-projections.json --output PRIVATE_REPORT.json
```

Omit `--replay` to use the existing REST transport (requires `FIRECRAWL_API_KEY`). A host connector can also inject a callable into `FirecrawlProvider`. Replay validates operation and selector and fails closed on missing/ambiguous receipts; it does not simulate network success. The R90 run uses actual connector-derived response projections, not a deployed autonomous host runtime. A catalog plan item contains `id`, `url`, `operation` (`catalog`, `map`, `crawl`) and optional bounds; the ledger tracks failures, pagination, partial coverage and crosswalk duplicates. No exhaustive catalog coverage is implied. 

Crosswalk rows contain `production_id`, `title`, `aliases`, `source` (`url`, `excerpt`, `reviewed`), optional `country`, `year`, `format`, and `relation` (`same`, `sequel`, `remake`, `edit`). Sequel/remake/edit rows require `parent_title`. Only reviewed identity assertions can advance to evidence retrieval. `reviewed_novel` is a reviewer assertion about the recovered ledger, not proof that a user has never seen the work. Evidence must separately support completion, mutual romance, happy ending, runtime, fit, non-erotic/non-coercive relationship and official viewing. No positive claims are inferred from catalog extraction; no quota padding.

Private checkpoints, catalog projections, research decisions, and user records must stay outside the public repository. Keep original canonical arrays unchanged; append research-only discoveries separately.
