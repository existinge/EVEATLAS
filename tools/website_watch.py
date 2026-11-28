#!/usr/bin/env python3
"""Read-only public website availability and content smoke check.

No credentials, publishing, site modification or browser automation.
Exit nonzero on failure for GitHub Actions alerting.
"""
import argparse
import json
import re
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlsplit

MAX_BYTES = 1024 * 1024

def check(url, timeout=12, expected=None):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("requires a public HTTPS URL without userinfo")
    start = time.monotonic()
    req = Request(url, headers={"User-Agent":"EVEATLAS-WebsiteWatch/1.0 (read-only health check)", "Accept":"text/html"})
    with urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
        status=response.status
        final_url=response.geturl()
        if urlsplit(final_url).scheme != "https":
            raise ValueError("redirect left HTTPS")
        body=response.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:
            raise ValueError("response exceeds 1MB limit")
        content=body.decode("utf-8", errors="replace")
        if status < 200 or status >= 400: raise ValueError(f"HTTP {status}")
        if expected and expected.lower() not in content.lower():
            raise ValueError("expected page text missing")
        if not re.search(r"<(?:html|!doctype html|head|body)(?:\\s|>)",content,re.I):
            raise ValueError("response does not appear to be HTML")
    return {"time_utc":datetime.now(timezone.utc).isoformat(),"url":url,
            "final_url":final_url,"status":"pass","http_status":status,
            "latency_seconds":round(time.monotonic()-start,3),"bytes_read":len(body)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",default="https://telstarhq.com/")
    p.add_argument("--timeout",type=float,default=12.0)
    p.add_argument("--expected",default="")
    args=p.parse_args()
    try:
        data=check(args.url,args.timeout,args.expected or None)
        code=0
    except (ValueError,URLError,HTTPError,OSError) as exc:
        data={"time_utc":datetime.now(timezone.utc).isoformat(),"url":args.url,"status":"fail","reason":str(exc)}
        code=1
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return code
if __name__=="__main__":sys.exit(main())
