# BL Engine × KissKH catalog adapter (experimental, R50)

**Branch:** `feat/bl-kisskh-catalog-r50` (isolated from `feat/atlas-deep-discovery-gates`).

**Purpose:** Add a *discovery-only* optional lead intake source. KissKH is an
unofficial catalog and **not an official broadcaster, licensed availability
authority, proof of streaming access, or proof that a show is a BL**. No
login/keys, streaming extraction, subtitle decryption, episode playback, or
DRM-bypass code belongs in this adapter.

## Mapped metadata endpoints

| Operation | Request |
| --- | --- |
| Browse | `GET /api/DramaList/List?page=1&type=0&sub=0&country=0&status=0&order=1&pageSize=40` |
| Search | `GET /api/DramaList/Search?q=love&type=0` |
| Detail | `GET /api/DramaList/Drama/4608?isq=false` |

The type parameter is retained verbatim (0 is not assumed to mean BL).
These are **unofficial/unversioned** endpoints inferred from site behavior and
third-party clients. The contract is not guaranteed. The default HTTPS host is
`kisskh.is`; `kisskh.nl` may be supplied as a configured base if necessary.
One invocation makes one request; there is no bulk spider, concurrent fetcher,
automatic pagination, or proxy/captcha evasion.

`4608` is a *schema smoke-test ID* (A Business Proposal), not a BL example.
Do not confuse the numeric ID with a canonical BL Engine identity.

## Commands

From the repository root:

```shell
python -m tools.kisskh_catalog --search "love" --type 0 --output /tmp/kisskh-leads.json
python -m tools.kisskh_catalog --list-page 1 --page-size 20 --output /tmp/kisskh-page.json
python -m tools.kisskh_catalog --detail 4608 --output /tmp/kisskh-4608.json
python -m unittest discover -s tests -p 'test_kisskh_catalog.py' -v
```

To apply your **private** title and alias exclusion index, export a JSON file
such as `/tmp/atlas-private-known.json` locally:

```json
{"known_titles":[
  {"title":"Known Japanese Drama","aliases":["日本語タイトル"],"status":"Already Seen"},
  {"title":"Existing Backlog Item","aliases":[],"status":"Maybe"}
]}
```

Then:

```shell
python -m tools.kisskh_catalog --search "love" \
  --known /tmp/atlas-private-known.json \
  --output /tmp/kisskh-screened.json
```

**Never commit personal watch history or statuses** to this public repository.
Import them only at runtime. All known titles—including Maybe, Watching,
Completed, Skip, and unknown-status entries—are blocked from fresh discovery.

## Gate and evidence semantics

`screening` is the output of `tools.deep_discovery.run()` with candidate
receipts and provided `known_titles`. Each candidate has:

- a tentative title, original/native aliases when available, and KissKH ID;
- `catalog_provenance.kind = unofficial_catalog_metadata_only`;
- **unknown** release, central M/M romance, consent, and payoff claims;
- no independently verified official viewing URLs or trusted evidence links.

Therefore catalog-only hits can be at most `research_lead`, **never**
`verified_candidate`. Independent official production/distributor evidence,
native-language story checks, identity audits, and access verification must
happen in a separate research step before R50 recommendation cards.

The site can list Korean/heterosexual dramas, films and anime too. An item
appearing there is *not* evidence of BL genre or suitability. The initial
list/search envelopes are handled defensively, and unexpected response
shapes raise `CatalogError` rather than silently fabricating records.

## Runtime limitations and privacy

- Source-of-truth for personal statuses is the private latest R49/R50 workbook,
  never this public repository; the adapter accepts a private exported JSON.
- The upstream API is undocumented, may change or restrict automated use,
  and was **not independently live-tested** in this environment.
- Respect site terms, low rate limits and access controls. Do not treat this
  as permission to fetch protected video, subtitles or tokens.
- Browser availability, account entitlement, subtitle availability and
  content licensing are **all unverified** by this module.
- Offline unit tests use injected fixtures. They test routing, JSON
  normalization, fail-closed identity behavior, and source URL restrictions.

## Verification / follow-up

1. Run offline unit tests and the existing `tests/test_deep_discovery.py`.
2. With site permission, perform one live list/search/detail smoke test in a
   controlled environment and save timestamped response field names without
   private data.
3. Improve schema adapters from actual fixtures. Re-run tests.
4. Export private R50 exclusions at runtime, dedupe aliases, and independently
   investigate promising leads against official sources and story reviews.
5. Never merge or describe candidates as validated BL solely from API hits.
