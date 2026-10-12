#!/usr/bin/env python3
"""localnode: run the paired local worker + decider described in node.json.

  python3 localnode.py start     start server, preload both models, keep awake, launch guard
  python3 localnode.py status    health, loaded models, memory/swap
  python3 localnode.py ensure    reload any missing model (e.g. after the guard shed the worker)
  python3 localnode.py stop      unload models, stop guard + caffeinate + the sidecar server we started
  python3 localnode.py guard     (internal) run the memory guard in the foreground

Stdlib only. All config lives in node.json. State/logs live in ~/.localnode (never in Git).
"""
import json, os, re, shutil, signal, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "node.json").read_text())
BIND_HOST = os.environ.get("LOCALNODE_HOST", CFG["server"]["host"])
PORT = int(os.environ.get("LOCALNODE_PORT", CFG["server"]["port"]))
BASE = f"http://127.0.0.1:{PORT}"
STATE = Path.home() / ".localnode"
WORKER, DECIDER = CFG["worker"]["model"], CFG["decider"]["model"]


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def lan_ip():
    return sh("ipconfig getifaddr en0 2>/dev/null || ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -1").strip() or "127.0.0.1"


def api(path, body=None, timeout=600):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def up():
    try:
        api("/api/version", timeout=2); return True
    except Exception:
        return False


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def find_binary():
    """Pinned sidecar first, then any system ollama that is new enough. Returns path or None."""
    cands = [os.environ.get("LOCALNODE_OLLAMA"),
             str(Path.home() / ".localnode" / f"ollama-{CFG['ollama']['pinned']}" / "ollama"),
             str(Path.home() / ".localllm" / f"ollama-{CFG['ollama']['pinned']}" / "ollama"),
             shutil.which("ollama")]
    for c in filter(None, cands):
        if Path(c).exists():
            out = sh(f"'{c}' --version 2>&1")
            versions = re.findall(r"(?:client )?version is ([\d.]+)", out)
            if versions and any(vtuple(v) >= vtuple(CFG["ollama"]["min_version"]) for v in versions):
                return c
    return None


def free_pct():
    m = re.search(r"free percentage:\s*(\d+)%", sh("memory_pressure -Q"))
    return int(m.group(1)) if m else 100


def swap_gb():
    m = re.search(r"used = ([\d.]+)([MG])", sh("sysctl -n vm.swapusage"))
    return 0.0 if not m else float(m.group(1)) / (1024 if m.group(2) == "M" else 1)


def loaded():
    try:
        return [m["name"] for m in api("/api/ps", timeout=3).get("models", [])]
    except Exception:
        return []


def preload(model, ctx=None):
    opts = {"num_ctx": ctx} if ctx else {}
    if model == DECIDER:  # decider is served via /v1/systemone; a trivial call loads it
        api("/v1/systemone", {"model": model, "state": "ping", "keep_alive": -1,
                              "questions": {"q": {"type": "noul", "instructions": "Is this text non-empty?"}}})
    else:
        api("/api/generate", {"model": model, "prompt": "", "keep_alive": -1, "options": opts})


def notify(msg):
    sh(f"osascript -e 'display notification \"{msg}\" with title \"localnode\"'")


def have_models():
    out = sh(f"curl -s {BASE}/api/tags")
    names = [m["name"] for m in json.loads(out or "{}").get("models", [])]
    return [m for m in (WORKER, DECIDER) if m not in names]


def start():
    STATE.mkdir(exist_ok=True)
    if not up():
        binary = find_binary()
        if not binary:
            sys.exit("No Ollama >= %s found. Run ./setup.sh first." % CFG["ollama"]["min_version"])
        env = {**os.environ, **CFG["env"], "OLLAMA_HOST": f"{BIND_HOST}:{PORT}"}
        p = subprocess.Popen([binary, "serve"], env=env, stdout=open(STATE / "server.log", "a"),
                             stderr=subprocess.STDOUT, start_new_session=True)
        (STATE / "server.pid").write_text(str(p.pid))
        for _ in range(40):
            if up(): break
            time.sleep(1)
        else:
            sys.exit(f"server did not start; see {STATE/'server.log'}")
    missing = have_models()
    if missing:
        sys.exit(f"models not pulled: {missing}. Run ./setup.sh")
    for m, c in ((DECIDER, None), (WORKER, CFG["worker"]["ctx"])):  # small one first
        print(f"loading {m} ...", flush=True); preload(m, c)
    (STATE / "baseline_swap").write_text(str(swap_gb()))
    for name, argv in (("caffeinate", ["caffeinate", "-i", "-m"]), ("guard", [sys.executable, str(HERE / "localnode.py"), "guard"])):
        pf = STATE / f"{name}.pid"
        if pf.exists():
            try: os.kill(int(pf.read_text()), 0); continue
            except OSError: pass
        p = subprocess.Popen(argv, stdout=open(STATE / f"{name}.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)
        pf.write_text(str(p.pid))
    print(f"ready: local={BASE}  LAN=http://{lan_ip()}:{PORT}  worker={WORKER} ({CFG['worker']['endpoint']})  decider={DECIDER} ({CFG['decider']['endpoint']})")
    status()


def guard():
    g = CFG["guard"]
    base = float((STATE / "baseline_swap").read_text()) if (STATE / "baseline_swap").exists() else swap_gb()
    print(f"guard: free<{g['free_pct_min']}% or swap growth>{g['swap_growth_gb_max']}GB (baseline {base:.1f}GB)", flush=True)
    strikes = 0
    while True:
        f, s = free_pct(), swap_gb()
        bad = f < g["free_pct_min"] or (s - base) > g["swap_growth_gb_max"]
        strikes = strikes + 1 if bad else 0
        if strikes >= g["strikes"] and WORKER in loaded():
            try: api("/api/generate", {"model": WORKER, "keep_alive": 0}, timeout=30)
            except Exception: pass
            msg = f"Shed worker {WORKER}: free={f}% swap_growth={s-base:.1f}GB. Decider kept. Run 'localnode.py ensure' when pressure clears."
            print(msg, flush=True); notify(msg); strikes = 0
        time.sleep(g["poll_s"])


def status():
    ok = up()
    print(f"server: {'UP' if ok else 'DOWN'} (local {BASE} | LAN http://{lan_ip()}:{PORT}) | loaded: {loaded() if ok else '-'} | free mem: {free_pct()}% | swap: {swap_gb():.2f}GB")


def ensure():
    if not up(): return start()
    cur = loaded()
    for m, c in ((DECIDER, None), (WORKER, CFG["worker"]["ctx"])):
        if not any(x.startswith(m.split(":")[0]) and (":" not in m or m in cur or m.split(":")[1] in x) for x in cur) and m not in cur:
            print("reloading", m); preload(m, c)
    status()


def stop():
    if up():
        for m in loaded():
            try: api("/api/generate", {"model": m, "keep_alive": 0}, timeout=30)
            except Exception: pass
    for name in ("guard", "caffeinate", "server"):
        pf = STATE / f"{name}.pid"
        if pf.exists():
            try: os.kill(int(pf.read_text()), signal.SIGTERM)
            except (ProcessLookupError, ValueError): pass
            pf.unlink()
    print("stopped"); status()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"start": start, "status": status, "ensure": ensure, "stop": stop, "guard": guard}.get(cmd, lambda: sys.exit(__doc__))()
