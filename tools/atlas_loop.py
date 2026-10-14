"""ATLAS LOOP: persistent bounded orchestration; stdlib only, local/safe by default."""
import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_treasurer as treasurer
from atlas_brain import Worker, choose_worker, retry_advice

DEFAULT_DB = Path(__file__).resolve().parents[1] / "private" / "atlas-loop.sqlite3"
TERMINAL = {"COMPLETE", "BLOCKED", "CANCELLED", "FAILED"}
LEVELS = {"read": 0, "prepare": 1, "workspace_write": 2, "external": 3, "irreversible": 4}
BACKOFF_BASE_SECONDS = 2
BACKOFF_MAX_SECONDS = 300
# Run-control transitions: action -> statuses it may be applied from.
CONTROL_FROM = {"pause": {"QUEUED", "RUNNING", "AWAITING_FINAL_REVIEW"},
                "resume": {"QUEUED", "RUNNING", "AWAITING_FINAL_REVIEW"},
                "cancel": {"QUEUED", "RUNNING", "AWAITING_FINAL_REVIEW", "BLOCKED"}}

def worker_registry(allow_commands=False):
    """Worker capabilities known to the runtime. Provider adapters are not
    configured, so they are listed as unavailable and never routed to."""
    return [Worker("local", frozenset({"local"}), True, 0, priority=10),
            Worker("command", frozenset({"unittest"}), bool(allow_commands), 0, priority=20),
            Worker("deepseek", frozenset({"llm"}), False, 0, priority=30),
            Worker("gemini", frozenset({"llm"}), False, 0, priority=40),
            Worker("codex", frozenset({"llm", "review"}), False, 0, priority=50)]

WORKER_CAPABILITIES = {"local": ["local"], "command": ["unittest"], "deepseek": ["llm"],
                       "gemini": ["llm"], "codex": ["llm"]}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def connect(path=DEFAULT_DB):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(p)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, objective TEXT NOT NULL,
      status TEXT NOT NULL, budget REAL NOT NULL, spent REAL NOT NULL DEFAULT 0,
      paused INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
      name TEXT NOT NULL, worker TEXT NOT NULL, state TEXT NOT NULL,
      deps TEXT NOT NULL, acceptance TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
      max_attempts INTEGER NOT NULL DEFAULT 3, artifact TEXT, error TEXT,
      updated TEXT NOT NULL, next_attempt_at TEXT, strategy TEXT);
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,
      task_id TEXT, kind TEXT NOT NULL, data TEXT NOT NULL, timestamp TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,
      action TEXT NOT NULL,level INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',
      decision_at TEXT);
    CREATE TABLE IF NOT EXISTS reviews(run_id TEXT PRIMARY KEY, verdict TEXT NOT NULL,
      reviewer TEXT NOT NULL, evidence TEXT NOT NULL, timestamp TEXT NOT NULL);
    """)
    cols = {r[1] for r in db.execute("PRAGMA table_info(tasks)")}
    for col in ("next_attempt_at", "strategy"):
        if col not in cols:  # upgrade databases created before backoff support
            db.execute(f"ALTER TABLE tasks ADD COLUMN {col} TEXT")
    treasurer.ensure_schema(db)
    return db

def log(db, run, task, kind, data):
    db.execute("INSERT INTO events(run_id,task_id,kind,data,timestamp) VALUES(?,?,?,?,?)",
               (run, task, kind, json.dumps(data), now()))

def validate_plan(tasks):
    if not tasks or not isinstance(tasks, list):
        raise ValueError("plan must contain tasks")
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task IDs")
    graph = {t["id"]: t.get("deps", []) for t in tasks}
    seen, visiting = set(), set()
    def visit(node):
        if node in visiting: raise ValueError("dependency cycle")
        if node in seen: return
        visiting.add(node)
        for dep in graph[node]:
            if dep not in graph: raise ValueError("unknown dependency " + dep)
            visit(dep)
        visiting.remove(node); seen.add(node)
    for node in graph: visit(node)
    for t in tasks:
        if t.get("worker") not in {"local", "command", "codex", "deepseek", "gemini"}:
            raise ValueError("unknown worker")
        if not isinstance(t.get("acceptance"), dict):
            raise ValueError("acceptance must be an object")
    return True

def create_run(db, objective, tasks, budget=2.0):
    validate_plan(tasks)
    treasurer.cents(budget)  # refuse invalid or negative limits
    rid = "run-" + uuid.uuid4().hex[:12]
    with db:
        db.execute("INSERT INTO runs(id,objective,status,budget,created) VALUES(?,?,?,?,?)",
                   (rid, objective, "QUEUED", budget, now()))
        for task in tasks:
            db.execute("""INSERT INTO tasks(id,run_id,name,worker,state,deps,acceptance,max_attempts,updated)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                       (rid + ":" + task["id"],rid,task.get("name",task["id"]),task["worker"],
                        "QUEUED",json.dumps(task.get("deps",[])),json.dumps(task["acceptance"]),
                        min(5,max(1,int(task.get("max_attempts",3)))),now()))
        log(db,rid,None,"created",{"task_count":len(tasks)})
    return rid

def request_approval(db,rid,action,level):
    if isinstance(level, str):
        if level not in LEVELS: raise ValueError("unknown approval level")
        level = LEVELS[level]
    if level not in LEVELS.values(): raise ValueError("unknown approval level")
    if level < LEVELS["external"]: raise ValueError("approval only for consequential actions")
    aid = "approval-" + uuid.uuid4().hex[:12]
    with db:
        db.execute("INSERT INTO approvals(id,run_id,action,level) VALUES(?,?,?,?)",(aid,rid,action,level))
        log(db,rid,None,"approval_requested",{"approval_id":aid,"action":action})
    return aid

def decide_approval(db,aid,allow):
    with db:
        row=db.execute("SELECT * FROM approvals WHERE id=?",(aid,)).fetchone()
        if not row or row["status"] != "PENDING": raise ValueError("approval missing or already decided")
        db.execute("UPDATE approvals SET status=?,decision_at=? WHERE id=?",("APPROVED" if allow else "DENIED",now(),aid))
        log(db,row["run_id"],None,"approval_decided",{"approval_id":aid,"approved":allow})

def execute(task, workspace, allow_commands=False, timeout=30):
    """Only 'local' runs by default. Commands require explicit opt-in and allowlist."""
    spec=json.loads(task["acceptance"])
    if task["worker"] == "local":
        data = spec.get("content", "local deterministic fixture")
        return {"text":data,"worker":"local"}
    if task["worker"] in {"codex","deepseek","gemini"}:
        raise RuntimeError(task["worker"]+" adapter not configured; provider execution not simulated")
    if not allow_commands:
        raise RuntimeError("command execution disabled (pass --allow-commands with a trusted plan)")
    argv = spec.get("argv")
    if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv):
        raise RuntimeError("command worker requires argv list")
    # Executing arbitrary commands is unsafe; constrained to Python test execution.
    if argv[:3] != [sys.executable, "-m", "unittest"]:
        raise RuntimeError("only python -m unittest is permitted")
    proc = subprocess.run(argv,cwd=workspace,timeout=timeout,capture_output=True,text=True,shell=False)
    if proc.returncode: raise RuntimeError("test exited "+str(proc.returncode)+": "+proc.stderr[-1200:])
    return {"text":proc.stdout[-2000:],"worker":"command","exit_code":proc.returncode}

def verify(task, result):
    spec=json.loads(task["acceptance"])
    text=result.get("text","")
    if "contains" in spec and spec["contains"] not in text:
        return False,"required string missing"
    if "equals" in spec and text != spec["equals"]:
        return False,"output mismatch"
    return True,"verified output contract"

def backoff_seconds(attempts, base=None):
    base = BACKOFF_BASE_SECONDS if base is None else base
    return min(BACKOFF_MAX_SECONDS, base * (2 ** max(0, attempts - 1)))

def failure_signatures(db, task_id):
    rows = db.execute("SELECT data FROM events WHERE task_id=? AND kind='repair_pending' ORDER BY id", (task_id,))
    return [json.loads(r["data"]).get("error", "")[:200] for r in rows]

def critical_incidents(db, rid):
    return [dict(r) for r in db.execute("SELECT severity, code FROM cost_incidents WHERE run_id=? AND severity='critical'", (rid,))]

def _fail_task(db, rid, task, reason):
    with db:
        db.execute("UPDATE tasks SET state='FAILED',next_attempt_at=NULL,updated=? WHERE id=?", (now(), task["id"]))
        log(db, rid, task["id"], "failed", {"reason": reason})

def _after_failure(db, rid, task, error, allow_commands, backoff_base, clock):
    """Record the failure, then ask atlas_brain what to do next."""
    with db:
        db.execute("UPDATE tasks SET state='REPAIR_PENDING',error=?,updated=? WHERE id=?", (error, now(), task["id"]))
        log(db, rid, task["id"], "repair_pending", {"error": error, "worker": task["worker"]})
    attempts = task["attempts"] + 1
    advice = retry_advice(attempts, task["max_attempts"], failure_signatures(db, task["id"]), critical_incidents(db, rid))
    if advice["action"] == "stop":
        with db:
            db.execute("UPDATE runs SET status='BLOCKED' WHERE id=?", (rid,))
            log(db, rid, task["id"], "blocked", {"reason": advice["reason"]})
        return
    if advice["action"] == "escalate":
        _fail_task(db, rid, task, advice["reason"]); return
    if advice["action"] == "switch_strategy":
        others = [w for w in worker_registry(allow_commands) if w.name != task["worker"]]
        route = choose_worker(WORKER_CAPABILITIES[task["worker"]], others,
                              treasurer.snapshot(db, rid)["available_cents"])
        if route["action"] != "route":
            _fail_task(db, rid, task, "repeated_identical_failure_no_alternative"); return
        with db:
            db.execute("UPDATE tasks SET worker=?,strategy=? WHERE id=?", (route["worker"], "switched:" + task["worker"], task["id"]))
            log(db, rid, task["id"], "strategy_switched", {"from": task["worker"], "to": route["worker"]})
    wait = backoff_seconds(attempts, backoff_base)
    due = (clock() + dt.timedelta(seconds=wait)).isoformat()
    with db:
        db.execute("UPDATE tasks SET next_attempt_at=? WHERE id=?", (due, task["id"]))
        log(db, rid, task["id"], "backoff", {"seconds": wait, "next_attempt_at": due})

def tick(db,rid,workspace=".",allow_commands=False,backoff_base=None,clock=None):
    clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
    run=db.execute("SELECT * FROM runs WHERE id=?",(rid,)).fetchone()
    if not run: raise ValueError("unknown run")
    if run["paused"] or run["status"] in TERMINAL or run["status"]=="AWAITING_FINAL_REVIEW":
        return run["status"]
    incidents = critical_incidents(db, rid)
    if incidents:
        with db:
            db.execute("UPDATE runs SET status='BLOCKED' WHERE id=?",(rid,))
            log(db,rid,None,"blocked",{"reason":"critical_state"})
        return "BLOCKED"
    tasks=db.execute("SELECT * FROM tasks WHERE run_id=? ORDER BY rowid",(rid,)).fetchall()
    completed={t["id"].split(":",1)[1] for t in tasks if t["state"]=="COMPLETE"}
    current=clock()
    for task in tasks:
        if task["state"] in {"COMPLETE","BLOCKED","FAILED"}: continue
        deps=json.loads(task["deps"])
        if not set(deps).issubset(completed):continue
        if task["next_attempt_at"] and dt.datetime.fromisoformat(task["next_attempt_at"]) > current:
            continue  # backing off
        if task["attempts"] >= task["max_attempts"]:
            _fail_task(db,rid,task,"retry_cap"); continue
        route = choose_worker(WORKER_CAPABILITIES[task["worker"]],
                              [w for w in worker_registry(allow_commands) if w.name == task["worker"]],
                              treasurer.snapshot(db,rid)["available_cents"])
        if route["action"] != "route" and task["worker"] != "local" and treasurer.snapshot(db,rid)["available_cents"] <= 0:
            with db:
                db.execute("UPDATE runs SET status='BLOCKED' WHERE id=?",(rid,))
                log(db,rid,task["id"],"blocked",{"reason":"budget"})
            return "BLOCKED"
        with db:
            db.execute("UPDATE tasks SET state='RUNNING',attempts=attempts+1,updated=? WHERE id=?",(now(),task["id"]))
            db.execute("UPDATE runs SET status='RUNNING' WHERE id=?",(rid,))
            log(db,rid,task["id"],"dispatch",{"worker":task["worker"],"route":route["action"]})
        try:
            result=execute(task,workspace,allow_commands)
            valid,reason=verify(task,result)
            if not valid: raise RuntimeError(reason)
            with db:
                db.execute("UPDATE tasks SET state='COMPLETE',artifact=?,error=NULL,next_attempt_at=NULL,updated=? WHERE id=?",
                           (json.dumps(result),now(),task["id"]))
                log(db,rid,task["id"],"verified",result)
        except (RuntimeError,subprocess.TimeoutExpired,OSError) as exc:
            _after_failure(db,rid,task,str(exc),allow_commands,backoff_base,clock)
        break
    run=db.execute("SELECT status FROM runs WHERE id=?",(rid,)).fetchone()
    if run["status"]=="BLOCKED": return "BLOCKED"
    states=[t["state"] for t in db.execute("SELECT state FROM tasks WHERE run_id=?",(rid,))]
    if all(s=="COMPLETE" for s in states):
        with db:
            db.execute("UPDATE runs SET status='AWAITING_FINAL_REVIEW' WHERE id=?",(rid,))
            log(db,rid,None,"awaiting_codex",{"requirement":"independent Codex final review"})
        return "AWAITING_FINAL_REVIEW"
    if "FAILED" in states:
        with db:
            db.execute("UPDATE runs SET status='FAILED' WHERE id=?",(rid,))
            log(db,rid,None,"run_failed",{"failed_tasks":states.count("FAILED")})
        return "FAILED"
    if "BLOCKED" in states:
        with db: db.execute("UPDATE runs SET status='BLOCKED' WHERE id=?",(rid,))
        return "BLOCKED"
    return "RUNNING"

def control(db, rid, action):
    """Pause, resume or cancel a run, enforcing valid status transitions."""
    if action not in CONTROL_FROM: raise ValueError("unknown control action")
    with db:
        run = db.execute("SELECT status, paused FROM runs WHERE id=?", (rid,)).fetchone()
        if not run: raise ValueError("unknown run")
        if run["status"] not in CONTROL_FROM[action]:
            raise ValueError(f"cannot {action} a run in status {run['status']}")
        if action == "pause":
            if run["paused"]: raise ValueError("run already paused")
            db.execute("UPDATE runs SET paused=1 WHERE id=?", (rid,))
        elif action == "resume":
            if not run["paused"]: raise ValueError("run is not paused")
            db.execute("UPDATE runs SET paused=0 WHERE id=?", (rid,))
        else:
            db.execute("UPDATE runs SET status='CANCELLED', paused=0 WHERE id=?", (rid,))
        log(db, rid, None, action, {"from_status": run["status"]})
    return db.execute("SELECT status, paused FROM runs WHERE id=?", (rid,)).fetchone()["status"]

STOP_STATUSES = TERMINAL | {"AWAITING_FINAL_REVIEW"}

def run_loop(db,rid,workspace=".",allow_commands=False,max_ticks=100,max_seconds=300,
             backoff_base=None,sleep=time.sleep,monotonic=time.monotonic,clock=None):
    """Tick on one connection until the run stops, is paused, or a safety cap trips.
    Waits for the earliest backoff deadline instead of busy-looping."""
    if max_ticks < 1 or max_seconds <= 0: raise ValueError("caps must be positive")
    clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
    started = monotonic(); ticks = 0; state = None
    while True:
        run = db.execute("SELECT status, paused FROM runs WHERE id=?", (rid,)).fetchone()
        if not run: raise ValueError("unknown run")
        if run["paused"]: return {"status": run["status"], "ticks": ticks, "stopped": "paused"}
        if run["status"] in STOP_STATUSES: return {"status": run["status"], "ticks": ticks, "stopped": "run_state"}
        if ticks >= max_ticks: return {"status": run["status"], "ticks": ticks, "stopped": "max_ticks"}
        remaining = max_seconds - (monotonic() - started)
        if remaining <= 0: return {"status": run["status"], "ticks": ticks, "stopped": "max_seconds"}
        state = tick(db, rid, workspace, allow_commands, backoff_base, clock); ticks += 1
        if state in STOP_STATUSES: continue
        pending = db.execute("""SELECT MIN(next_attempt_at) FROM tasks WHERE run_id=? AND state='REPAIR_PENDING'
                             AND next_attempt_at IS NOT NULL""", (rid,)).fetchone()[0]
        if pending:
            wait = (dt.datetime.fromisoformat(pending) - clock()).total_seconds()
            if wait > 0:
                remaining = max_seconds - (monotonic() - started)
                if wait > remaining:
                    return {"status": state, "ticks": ticks, "stopped": "max_seconds"}
                sleep(wait)

def final_review(db,rid,verdict,evidence,reviewer="codex"):
    if reviewer!="codex": raise ValueError("final reviewer must be Codex")
    if verdict not in {"approved","changes_required","blocked"}: raise ValueError("invalid verdict")
    if not evidence.strip(): raise ValueError("review evidence required")
    row=db.execute("SELECT status FROM runs WHERE id=?",(rid,)).fetchone()
    if not row or row["status"]!="AWAITING_FINAL_REVIEW": raise ValueError("run not awaiting final review")
    with db:
        db.execute("INSERT OR REPLACE INTO reviews VALUES(?,?,?,?,?)",(rid,verdict,reviewer,evidence,now()))
        status="COMPLETE" if verdict=="approved" else "BLOCKED"
        db.execute("UPDATE runs SET status=? WHERE id=?",(status,rid))
        log(db,rid,None,"codex_review",{"verdict":verdict,"evidence":evidence})
    return status

def status(db,rid):
    run=db.execute("SELECT * FROM runs WHERE id=?",(rid,)).fetchone()
    if not run: raise ValueError("unknown run")
    tasks=[dict(t) for t in db.execute("SELECT * FROM tasks WHERE run_id=?",(rid,))]
    return {"run":dict(run),"tasks":tasks,"treasurer":treasurer.advise(db,rid),
            "review":next((dict(r) for r in db.execute("SELECT * FROM reviews WHERE run_id=?",(rid,))),None)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",default=str(DEFAULT_DB))
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("start");a.add_argument("plan");a.add_argument("--budget",type=float,default=2.0)
    a=sub.add_parser("tick");a.add_argument("run");a.add_argument("--allow-commands",action="store_true");a.add_argument("--workspace",default=".")
    a=sub.add_parser("run");a.add_argument("run");a.add_argument("--allow-commands",action="store_true");a.add_argument("--workspace",default=".")
    a.add_argument("--max-ticks",type=int,default=100);a.add_argument("--max-seconds",type=float,default=300)
    for name in ("status","pause","resume","cancel"):
        a=sub.add_parser(name);a.add_argument("run")
    a=sub.add_parser("review");a.add_argument("run");a.add_argument("verdict",choices=["approved","changes_required","blocked"]);a.add_argument("--evidence",required=True)
    a=sub.add_parser("approve");a.add_argument("approval")
    a=sub.add_parser("deny");a.add_argument("approval")
    a=sub.add_parser("budget");a.add_argument("run")
    a=sub.add_parser("reserve");a.add_argument("run");a.add_argument("task");a.add_argument("provider");a.add_argument("model");a.add_argument("maximum_cost");a.add_argument("--id")
    a=sub.add_parser("settle");a.add_argument("reservation");a.add_argument("actual_cost");a.add_argument("--source",choices=["provider_reported","invoice_verified","gateway_metered"],required=True)
    a=sub.add_parser("uncertain");a.add_argument("reservation");a.add_argument("reason")
    a=sub.add_parser("release");a.add_argument("reservation");a.add_argument("reason")
    args=p.parse_args()
    db=connect(args.db)
    try:
        if args.action=="start":
            d=json.loads(Path(args.plan).read_text(encoding="utf-8"))
            out={"run_id":create_run(db,d["objective"],d["tasks"],args.budget)}
        elif args.action=="tick": out={"status":tick(db,args.run,args.workspace,args.allow_commands)}
        elif args.action=="run":out=run_loop(db,args.run,args.workspace,args.allow_commands,args.max_ticks,args.max_seconds)
        elif args.action=="status":out=status(db,args.run)
        elif args.action=="budget":out=treasurer.advise(db,args.run)
        elif args.action=="reserve":out={"reservation_id":treasurer.reserve(db,args.run,args.task,args.provider,args.model,args.maximum_cost,args.id)}
        elif args.action=="settle":out=treasurer.reconcile(db,args.reservation,args.actual_cost,args.source)
        elif args.action=="uncertain":
            treasurer.mark_uncertain(db,args.reservation,args.reason);out={"reservation":args.reservation,"status":"uncertain"}
        elif args.action=="release":
            treasurer.release(db,args.reservation,args.reason);out={"reservation":args.reservation,"status":"released"}
        elif args.action=="review":out={"status":final_review(db,args.run,args.verdict,args.evidence)}
        elif args.action in {"pause","resume","cancel"}:
            out={"action":args.action,"run":args.run,"status":control(db,args.run,args.action)}
        else:
            decide_approval(db,args.approval,args.action=="approve");out={"approval":args.approval,"decision":args.action}
        print(json.dumps(out,indent=2));return 0
    except (ValueError,KeyError,OSError,sqlite3.Error,json.JSONDecodeError) as exc:
        print("atlas-loop: "+str(exc),file=sys.stderr);return 1
    finally: db.close()
if __name__=="__main__":sys.exit(main())
