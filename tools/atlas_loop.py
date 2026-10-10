"""ATLAS LOOP: persistent bounded orchestration; stdlib only, local/safe by default."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

DEFAULT_DB = Path(__file__).resolve().parents[1] / "private" / "atlas-loop.sqlite3"
TERMINAL = {"COMPLETE", "BLOCKED", "CANCELLED", "FAILED"}
MODEL_PREFERENCES = {"builder": ["deepseek-flash", "gemini-flash"], "planner": ["gemini-flash", "deepseek-flash"], "final_reviewer": ["codex"]}
LEVELS = {"read": 0, "prepare": 1, "workspace_write": 2, "external": 3, "irreversible": 4}

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
      updated TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,
      task_id TEXT, kind TEXT NOT NULL, data TEXT NOT NULL, timestamp TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,
      action TEXT NOT NULL,level INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',
      decision_at TEXT);
    CREATE TABLE IF NOT EXISTS reviews(run_id TEXT PRIMARY KEY, verdict TEXT NOT NULL,
      reviewer TEXT NOT NULL, evidence TEXT NOT NULL, timestamp TEXT NOT NULL);
    """)
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
    if budget < 0: raise ValueError("negative budget")
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
    if level < 3: raise ValueError("approval only for consequential actions")
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

def tick(db,rid,workspace=".",allow_commands=False):
    run=db.execute("SELECT * FROM runs WHERE id=?",(rid,)).fetchone()
    if not run: raise ValueError("unknown run")
    if run["paused"] or run["status"] in TERMINAL or run["status"]=="AWAITING_FINAL_REVIEW":
        return run["status"]
    tasks=db.execute("SELECT * FROM tasks WHERE run_id=? ORDER BY rowid",(rid,)).fetchall()
    completed={t["id"].split(":",1)[1] for t in tasks if t["state"]=="COMPLETE"}
    for task in tasks:
        if task["state"] in {"COMPLETE","BLOCKED"}: continue
        deps=json.loads(task["deps"])
        if not set(deps).issubset(completed):continue
        if task["attempts"] >= task["max_attempts"]:
            with db:
                db.execute("UPDATE tasks SET state='BLOCKED',updated=? WHERE id=?",(now(),task["id"]))
                log(db,rid,task["id"],"blocked",{"reason":"retry cap"})
            continue
        if run["spent"] >= run["budget"] and task["worker"]!="local":
            with db:
                db.execute("UPDATE runs SET status='BLOCKED' WHERE id=?",(rid,))
                log(db,rid,task["id"],"blocked",{"reason":"budget"})
            return "BLOCKED"
        with db:
            db.execute("UPDATE tasks SET state='RUNNING',attempts=attempts+1,updated=? WHERE id=?",(now(),task["id"]))
            db.execute("UPDATE runs SET status='RUNNING' WHERE id=?",(rid,))
            log(db,rid,task["id"],"dispatch",{"worker":task["worker"]})
        try:
            result=execute(task,workspace,allow_commands)
            valid,reason=verify(task,result)
            if not valid: raise RuntimeError(reason)
            with db:
                db.execute("UPDATE tasks SET state='COMPLETE',artifact=?,error=NULL,updated=? WHERE id=?",
                           (json.dumps(result),now(),task["id"]))
                log(db,rid,task["id"],"verified",result)
        except (RuntimeError,subprocess.TimeoutExpired,OSError) as exc:
            with db:
                db.execute("UPDATE tasks SET state='REPAIR_PENDING',error=?,updated=? WHERE id=?",(str(exc),now(),task["id"]))
                log(db,rid,task["id"],"repair_pending",{"error":str(exc)})
        break
    tasks=db.execute("SELECT state FROM tasks WHERE run_id=?",(rid,)).fetchall()
    states=[t["state"] for t in tasks]
    if all(s=="COMPLETE" for s in states):
        with db:
            db.execute("UPDATE runs SET status='AWAITING_FINAL_REVIEW' WHERE id=?",(rid,))
            log(db,rid,None,"awaiting_codex",{"requirement":"independent Codex final review"})
        return "AWAITING_FINAL_REVIEW"
    if "BLOCKED" in states:
        with db: db.execute("UPDATE runs SET status='BLOCKED' WHERE id=?",(rid,))
        return "BLOCKED"
    return "RUNNING"

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
    return {"run":dict(run),"tasks":tasks,
            "review":next((dict(r) for r in db.execute("SELECT * FROM reviews WHERE run_id=?",(rid,))),None)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",default=str(DEFAULT_DB))
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("start");a.add_argument("plan");a.add_argument("--budget",type=float,default=2.0)
    a=sub.add_parser("tick");a.add_argument("run");a.add_argument("--allow-commands",action="store_true");a.add_argument("--workspace",default=".")
    for name in ("status","pause","resume","cancel"):
        a=sub.add_parser(name);a.add_argument("run")
    a=sub.add_parser("review");a.add_argument("run");a.add_argument("verdict",choices=["approved","changes_required","blocked"]);a.add_argument("--evidence",required=True)
    a=sub.add_parser("approve");a.add_argument("approval")
    a=sub.add_parser("deny");a.add_argument("approval")
    args=p.parse_args()
    db=connect(args.db)
    try:
        if args.action=="start":
            d=json.loads(Path(args.plan).read_text(encoding="utf-8"))
            out={"run_id":create_run(db,d["objective"],d["tasks"],args.budget)}
        elif args.action=="tick": out={"status":tick(db,args.run,args.workspace,args.allow_commands)}
        elif args.action=="status":out=status(db,args.run)
        elif args.action=="review":out={"status":final_review(db,args.run,args.verdict,args.evidence)}
        elif args.action in {"pause","resume","cancel"}:
            with db:
                db.execute("UPDATE runs SET paused=?,status=? WHERE id=?",(int(args.action=="pause"),"CANCELLED" if args.action=="cancel" else "RUNNING",args.run))
                log(db,args.run,None,args.action,{})
            out={"action":args.action,"run":args.run}
        else:
            decide_approval(db,args.approval,args.action=="approve");out={"approval":args.approval,"decision":args.action}
        print(json.dumps(out,indent=2));return 0
    except (ValueError,KeyError,OSError,sqlite3.Error,json.JSONDecodeError) as exc:
        print("atlas-loop: "+str(exc),file=sys.stderr);return 1
    finally: db.close()
if __name__=="__main__":sys.exit(main())
