"""Bounded unauthenticated reachability probe for historical MyDramaList API v1.

This verifies DNS/TLS/HTTP response only. Never includes credentials or
claims a usable authenticated API. One GET, no retries or scraping.
"""
import json
import socket
import ssl
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def main():
    url="https://api.mydramalist.com/v1/genres"
    result={"source":"MyDramaList official 2019-2020 v1 docs",
            "host":"api.mydramalist.com","path":"/v1/genres",
            "credential_supplied":False}
    try:
        infos=socket.getaddrinfo("api.mydramalist.com",443,type=socket.SOCK_STREAM)
        result["dns"]="resolved"
        result["address_count"]=len(infos)
    except OSError as e:
        result.update(dns="failed",reason=type(e).__name__)
        print(json.dumps(result,indent=2))
        return 0
    request=Request(url,headers={"Accept":"application/json","User-Agent":"ATLAS-BL-API-HealthCheck/0.1"})
    try:
        with urlopen(request,timeout=8) as response:
            result.update(http_status=response.status,response_type=response.headers.get("content-type","unknown"),api_reachable=True)
    except HTTPError as exc:
        result.update(http_status=exc.code,response_type=exc.headers.get("content-type","unknown"),api_reachable=True)
    except (URLError,TimeoutError,ssl.SSLError,OSError) as exc:
        result.update(api_reachable=False,reason=type(exc).__name__)
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
