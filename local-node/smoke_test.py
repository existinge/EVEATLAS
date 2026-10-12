#!/usr/bin/env python3
"""Verify the node end to end. Exit 0 only if every check passes. No paid APIs."""
import json, subprocess, sys
import client

results = []
def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, f"{type(e).__name__}: {e}"
    results.append(ok); print(("PASS" if ok else "FAIL"), "-", name, "|", detail)

def models_loaded():
    ps = client._post  # noqa
    import urllib.request
    d = json.loads(urllib.request.urlopen(client.BASE + "/api/ps", timeout=5).read())
    names = [m["name"] for m in d.get("models", [])]
    want = [client.CFG["worker"]["model"], client.CFG["decider"]["model"]]
    return all(w in names for w in want), f"loaded={names}"

def worker_tool_call():
    tools = [{"type": "function", "function": {"name": "search", "description": "Search the web",
              "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
    r = client.work("Find the weather in Paris.", tools=tools)
    tc = r["tool_calls"]
    return bool(tc) and tc[0]["function"]["name"] == "search" and "query" in tc[0]["function"]["arguments"], f"{r['tps']} tok/s, call={tc[0]['function'] if tc else None}"

def decider():
    q = {"cls": {"type": "choice", "instructions": "Is this email a rejection or an interview request?",
                 "criteria": {"interview_request": "wants to schedule", "rejection": "declines the candidate"}}}
    a = client.decide("Thank you for applying. Unfortunately we are moving forward with other candidates.", q)["cls"]
    return a["choice"] == "rejection" and abs(sum(a["probabilities"].values()) - 1) < 0.01, f"{a['choice']} p={max(a['probabilities'].values()):.2f}"

def memory():
    out = subprocess.run("sysctl -n vm.swapusage", shell=True, capture_output=True, text=True).stdout.strip()
    return True, out

check("both models resident", models_loaded)
check("worker native tool call", worker_tool_call)
check("decider typed decision", decider)
check("memory snapshot (informational)", memory)
print("\nNODE OK" if all(results) else "\nNODE NOT OK"); sys.exit(0 if all(results) else 1)
