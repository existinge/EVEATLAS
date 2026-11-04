"""KissKH discovery-only catalog adapter for ATLAS BL Engine.

Unofficial endpoints are changeable and are NOT licensing, romance or playback
evidence. No streams, episodes, subtitle decryption, keys or bypasses.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from tools.deep_discovery import run as evidence_gate

ALLOWED_HOSTS = frozenset({"kisskh.is", "kisskh.nl"})
MAX_BYTES = 2_000_000


class CatalogError(ValueError):
    """Bad upstream schema, unsupported source URL or unsafe input."""


def _valid_base(base_url: str) -> str:
    p = urlsplit(base_url)
    if (p.scheme != "https" or p.hostname not in ALLOWED_HOSTS or
            p.username or p.password or p.port or p.path not in ("", "/") or
            p.query or p.fragment):
        raise CatalogError("base URL must be an HTTPS KissKH catalog host")
    return urlunsplit((p.scheme, p.netloc, "", "", ""))


def _http_get(url: str) -> object:
    request = Request(url, headers={"Accept": "application/json",
                                    "User-Agent": "ATLAS-BL-CatalogResearch/0.1"})
    with urlopen(request, timeout=12) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise CatalogError("catalog response exceeds size cap")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError("catalog did not return valid JSON") from exc


class KissKHCatalog:
    """A single-request client. A transport can be injected for offline tests."""

    def __init__(self, base_url="https://kisskh.is", transport=None):
        self.base_url = _valid_base(base_url)
        self.transport = transport or _http_get

    def _get(self, path, params):
        url = self.base_url + path + "?" + urlencode(params)
        return self.transport(url), url

    def list_page(self, page=1, page_size=40, media_type=0):
        if not (isinstance(page, int) and 1 <= page <= 10000):
            raise CatalogError("page out of range")
        if not (isinstance(page_size, int) and 1 <= page_size <= 40):
            raise CatalogError("page size must be 1..40")
        if not (isinstance(media_type, int) and 0 <= media_type <= 10):
            raise CatalogError("invalid media type")
        return self._get("/api/DramaList/List", {
            "page": page, "type": media_type, "sub": 0, "country": 0,
            "status": 0, "order": 1, "pageSize": page_size
        })

    def search(self, query, media_type=0):
        if not isinstance(query, str) or not query.strip() or len(query) > 120:
            raise CatalogError("query must contain 1..120 characters")
        if not (isinstance(media_type, int) and 0 <= media_type <= 10):
            raise CatalogError("invalid media type")
        return self._get("/api/DramaList/Search",
                         {"q": query.strip(), "type": media_type})

    def drama(self, drama_id, isq=False):
        if (isinstance(drama_id, bool) or
                not str(drama_id).isdigit() or
                not (1 <= int(drama_id) <= 999999999)):
            raise CatalogError("drama ID must be a positive integer")
        if not isinstance(isq, bool):
            raise CatalogError("isq must be Boolean")
        return self._get("/api/DramaList/Drama/" + str(int(drama_id)),
                         {"isq": str(isq).lower()})


def _extract_rows(payload, detail=False):
    """Accept observed envelope variants; fail closed on unknown shapes."""
    body = payload.get("data", payload) if isinstance(payload, dict) else payload
    if detail:
        if isinstance(body, dict) and body.get("id") is not None:
            return [body]
        raise CatalogError("detail JSON has no identifiable drama")
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for field in ("items", "results", "list", "dramas", "data"):
            if isinstance(body.get(field), list):
                return body[field]
    raise CatalogError("unrecognized list/search response shape")


def _aliases(item):
    values = []
    for field in ("originalTitle", "nativeTitle", "otherTitle", "otherTitles",
                  "alternativeTitle", "alternativeTitles", "aka", "aliases"):
        val = item.get(field)
        if isinstance(val, str):
            values.extend(x.strip() for x in val.replace("|", ",").split(","))
        elif isinstance(val, list):
            values.extend(x.strip() for x in val if isinstance(x, str))
    title = str(item.get("title") or item.get("name") or "").strip()
    return list(dict.fromkeys(x for x in values if x and x.casefold() != title.casefold()))


def normalize(raw, source_url):
    """Return a provisional receipt, NOT a verified or BL-classified title."""
    if not isinstance(raw, dict):
        raise CatalogError("catalog item must be a JSON object")
    title = raw.get("title") or raw.get("name")
    identifier = raw.get("id")
    if not isinstance(title, str) or not title.strip():
        raise CatalogError("catalog item lacks a title")
    if (identifier is None or isinstance(identifier, bool) or
            not str(identifier).isdigit()):
        raise CatalogError("catalog item lacks a valid drama ID")
    return {
        "title": title.strip(),
        "aliases": _aliases(raw),
        "released": None,
        "central_mm_romance": None,
        "healthy_consent": None,
        "romantic_payoff": None,
        "sources": [],
        "catalog_provenance": {
            "provider": "kisskh",
            "kind": "unofficial_catalog_metadata_only",
            "id": int(identifier),
            "query_url": source_url
        }
    }


def screen(payload, source_url, known_titles=None, detail=False):
    rows = _extract_rows(payload, detail=detail)
    candidates = [normalize(row, source_url) for row in rows]
    # Existing offline ATLAS gate blocks known aliases and leaves all unsupported
    # release/romance/consent/payoff claims explicitly pending.
    checked = evidence_gate({"known_titles": known_titles or [],
                             "candidates": candidates})
    return {
        "provider": "kisskh", "source_url": source_url,
        "metadata_only": True, "live_playback_verified": False,
        "candidates": candidates, "screening": checked
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", help="catalog keyword query")
    group.add_argument("--list-page", type=int, help="catalog page (1-based)")
    group.add_argument("--detail", type=int, help="drama ID")
    parser.add_argument("--base-url", default="https://kisskh.is")
    parser.add_argument("--type", type=int, default=0)
    parser.add_argument("--page-size", type=int, default=40)
    parser.add_argument("--known", type=Path,
                        help="private JSON with known_titles array; never commit it")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    known = []
    if args.known:
        private = json.loads(args.known.read_text(encoding="utf-8"))
        known = private["known_titles"] if isinstance(private, dict) else private
        if not isinstance(known, list):
            parser.error("--known must contain an array of tracked title records")
    client = KissKHCatalog(args.base_url)
    if args.search is not None:
        payload, url = client.search(args.search, args.type)
    elif args.list_page is not None:
        payload, url = client.list_page(args.list_page, args.page_size, args.type)
    else:
        payload, url = client.drama(args.detail)
    result = screen(payload, url, known, detail=args.detail is not None)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
