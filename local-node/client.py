#!/usr/bin/env python3
"""Minimal client for the paired local node. Import or run `python3 client.py`.

work(prompt, tools=None)  -> dict(message, tool_calls, tokens, tps)   # cheap worker; DRAFT output only
decide(state, questions)  -> dict(question -> answer fields)         # typed probabilities; ADVISORY only
"""
import json, os, time, urllib.request
from pathlib import Path

CFG = json.loads((Path(__file__).resolve().parent / "node.json").read_text())
BASE = f"http://{CFG['server']['host']}:{os.environ.get('LOCALNODE_PORT', CFG['server']['port'])}"


def _post(path, body, timeout=600):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def work(prompt, tools=None, system=None, max_tokens=None, temperature=0):
    w = CFG["worker"]
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": w["model"], "stream": False, "messages": msgs,
            "options": {"num_ctx": w["ctx"], "temperature": temperature, "num_predict": max_tokens or max(w["min_num_predict"], 1500)}}
    if tools: body["tools"] = tools
    d = _post("/api/chat", body)
    m = d["message"]
    return {"content": m.get("content", ""), "thinking": m.get("thinking", ""), "tool_calls": m.get("tool_calls") or [],
            "tokens": d["eval_count"], "tps": round(d["eval_count"] / d["eval_duration"] * 1e9, 1)}


def decide(state, questions):
    d = _post("/v1/systemone", {"model": CFG["decider"]["model"], "state": state, "questions": questions})
    return d["answers"]


if __name__ == "__main__":
    q = {"cls": {"type": "choice", "instructions": "Is this email a rejection or an interview request?",
                 "criteria": {"interview_request": "wants to schedule", "rejection": "declines the candidate"}}}
    t = time.time(); a = decide("We'd like to schedule a call on Thursday.", q)
    print("decide:", a["cls"]["choice"], f"({(time.time()-t)*1000:.0f} ms)")
