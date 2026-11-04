"""One-shot, metadata-only public KissKH endpoint smoke test for CI.

Three GET requests maximum, no retries, no protected episodes, no cookies or keys.
Emits response status and JSON envelope keys only; never logs full records.
This is a separate *integration smoke*, not part of the offline unit suite.
"""
import json
import os
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from tools.kisskh_catalog import KissKHCatalog, CatalogError, _extract_rows

def main():
    c = KissKHCatalog()
    calls = [
        ("list", lambda: c.list_page(page=1, page_size=2)),
        ("search", lambda: c.search("love")),
        ("detail", lambda: c.drama(4608)),
    ]
    outcomes = []
    for name, make in calls:
        try:
            # Same transport implementation as production; default timeout=12s.
            payload, url = make()
            rows = _extract_rows(payload, detail=name == "detail")
            sample = rows[0] if rows else {}
            keys = sorted(sample)[:25] if isinstance(sample, dict) else []
            outcomes.append({"endpoint":name, "result":"ok", "row_count":len(rows),
                             "first_record_fields":keys})
        except (HTTPError, URLError, TimeoutError, CatalogError, ValueError, ssl.SSLError) as exc:
            # Don't include URL or body: a proxy might put credentials in an error.
            msg = f"{type(exc).__name__}"
            if isinstance(exc, HTTPError):
                msg += f" (HTTP {exc.code})"
            elif isinstance(exc, CatalogError):
                msg += f" ({str(exc)[:90]})"
            outcomes.append({"endpoint":name, "result":"unverified", "reason":msg})
    print(json.dumps(outcomes, indent=2, ensure_ascii=False))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("### KissKH public catalog smoke test\n\n")
            fh.write("| Endpoint | Result | Observed schema |\n|---|---|---|\n")
            for o in outcomes:
                fields = ", ".join(o.get("first_record_fields", [])) or o.get("reason", "no rows")
                fh.write(f"| {o['endpoint']} | {o['result']} | `{fields}` |\n")
            fh.write("\nNo playback, decryption, entitlement or BL assertions.\n")
    return 0 if all(o["result"] == "ok" for o in outcomes) else 1

if __name__ == "__main__":
    sys.exit(main())
