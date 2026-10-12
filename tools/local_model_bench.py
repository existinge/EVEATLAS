#!/usr/bin/env python3
"""Dependency-free local model benchmark for an Ollama endpoint (decode/prefill/load + native tool-call check).

Usage: python tools/local_model_bench.py MODEL [MODEL ...] [--ctx 4096] [--append-log data/local_model_bench.jsonl]
Runs one model at a time (keep_alive=0 unloads after each) and records swap growth. Costs \\$0 API spend.
NOT a quality benchmark: the tool-call check is only a smoke test.
"""
import argparse, json, re, subprocess, sys, time, urllib.request
HOST = "http://127.0.0.1:11434"

def call(model, prompt, ctx, n, fmt=None):
    body = {"model": model, "prompt": prompt, "stream": False, "keep_alive": 0,
            "options": {"num_ctx": ctx, "num_predict": n, "temperature": 0}}
    if fmt: body["format"] = fmt
    req = urllib.request.Request(HOST + "/api/generate", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=1200).read())

def swap_gb():
    m = re.search(r"used = ([\d.]+)([MG])", subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout)
    return float(m.group(1)) / (1024 if m.group(2) == "M" else 1) if m else 0.0

def bench(model, ctx):
    s0 = swap_gb()
    d = call(model, "Write a Python function that merges overlapping intervals, with a short explanation.", ctx, 200)
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model, "ctx": ctx,
           "decode_tps": round(d["eval_count"] / d["eval_duration"] * 1e9, 1),
           "prefill_tps": round(d["prompt_eval_count"] / max(d["prompt_eval_duration"], 1) * 1e9, 1),
           "load_s": round(d["load_duration"] / 1e9, 1)}
    try:  # native tool-calling smoke test (model-agnostic schema; checks name + required arg)
        tools = [{"type": "function", "function": {"name": "search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
                 {"type": "function", "function": {"name": "read_file", "description": "Read a file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
        cases = [("Find the weather in Paris.", "search", "query"), ("Show me the contents of /etc/hosts", "read_file", "path")]
        ok = 0
        for q, name, arg in cases:
            body = {"model": model, "stream": False, "keep_alive": 0, "options": {"num_ctx": ctx, "num_predict": 1500, "temperature": 0}, "tools": tools, "messages": [{"role": "user", "content": q}]}
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
            tc = json.loads(urllib.request.urlopen(req, timeout=1200).read())["message"].get("tool_calls") or []
            ok += bool(tc) and tc[0]["function"]["name"] == name and arg in tc[0]["function"]["arguments"]
        row["tool_ok"] = f"{ok}/{len(cases)}"
    except Exception as e:
        row["tool_ok"] = f"error:{type(e).__name__}"
    row["swap_delta_gb"] = round(swap_gb() - s0, 2)
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("models", nargs="+"); ap.add_argument("--ctx", type=int, default=4096)
    ap.add_argument("--append-log"); a = ap.parse_args()
    for m in a.models:
        r = bench(m, a.ctx); print(json.dumps(r))
        if a.append_log:
            with open(a.append_log, "a") as f: f.write(json.dumps(r) + "\n")
