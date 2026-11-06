"""ATLAS Treasurer: transactional cost reservations and usage reconciliation.

Runtime-owned accounting. Worker-reported numbers are untrusted until reconciled.
No API calls, billing access, or money movement. Standard-library only.
"""
from decimal import Decimal, InvalidOperation, ROUND_UP
from datetime import datetime, timezone
import json
import sqlite3
import uuid

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def cents(value):
    try:
        amount=Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("invalid monetary amount") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("amount must be finite and nonnegative")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_UP))

def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS cost_reservations(
        reservation_id TEXT PRIMARY KEY, run_id TEXT NOT NULL,
        task_id TEXT, provider TEXT NOT NULL, model TEXT NOT NULL,
        reserved_cents INTEGER NOT NULL CHECK(reserved_cents>=0),
        charged_cents INTEGER,
        state TEXT NOT NULL CHECK(state IN ('reserved','settled','released','uncertain')),
        source TEXT, input_tokens INTEGER, output_tokens INTEGER,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_cost_reservations_run ON cost_reservations(run_id);
    CREATE TABLE IF NOT EXISTS cost_incidents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,
        severity TEXT NOT NULL, code TEXT NOT NULL, context TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

def _run(db, run_id):
    row=db.execute("SELECT budget FROM runs WHERE id=?",(run_id,)).fetchone()
    if row is None:
        raise ValueError("unknown run")
    return cents(row["budget"] if hasattr(row, "keys") else row[0])

def snapshot(db, run_id):
    limit=_run(db,run_id)
    rows=db.execute("""SELECT state,reserved_cents,charged_cents
        FROM cost_reservations WHERE run_id=?""",(run_id,)).fetchall()
    committed=sum((r["charged_cents"] or 0) for r in rows if r["state"]=="settled")
    held=sum(r["reserved_cents"] for r in rows if r["state"] in ("reserved","uncertain"))
    return {"run_id":run_id,"limit_cents":limit,"settled_cents":committed,
            "held_cents":held,"available_cents":max(0,limit-committed-held),
            "over_budget":committed+held>limit}

def reserve(db,run_id,task_id,provider,model,max_cost,reservation_id=None):
    """Atomic across SQLite connections. Caller must use a shared durable DB."""
    amount=cents(max_cost)
    if amount==0:
        raise ValueError("paid call requires nonzero upper cost reservation")
    if not provider or not model:
        raise ValueError("provider/model required")
    rid=reservation_id or "cost-"+uuid.uuid4().hex
    db.execute("BEGIN IMMEDIATE")
    try:
        existing=db.execute("SELECT * FROM cost_reservations WHERE reservation_id=?",(rid,)).fetchone()
        if existing is not None:
            if (existing["run_id"],existing["task_id"],existing["provider"],existing["model"],existing["reserved_cents"]) != (run_id,task_id,provider,model,amount):
                raise ValueError("reservation ID already used with different request")
            db.commit()
            return rid
        state=snapshot(db,run_id)
        if state["available_cents"]<amount:
            raise ValueError("budget exceeded; new dispatch denied")
        db.execute("""INSERT INTO cost_reservations
          (reservation_id,run_id,task_id,provider,model,reserved_cents,state,created_at,updated_at)
          VALUES(?,?,?,?,?,?,'reserved',?,?)""",
          (rid,run_id,task_id,provider,model,amount,utcnow(),utcnow()))
        db.commit()
        return rid
    except Exception:
        db.rollback()
        raise

def reconcile(db,reservation_id,actual_cost,source,input_tokens=None,output_tokens=None):
    """Provider bill or verified metering only. Never default missing data to zero."""
    if source not in {"provider_reported","invoice_verified","gateway_metered"}:
        raise ValueError("unverified source; use mark_uncertain instead")
    charge=cents(actual_cost)
    for token in (input_tokens,output_tokens):
        if token is not None and (type(token) is not int or token<0):
            raise ValueError("token counts must be nonnegative integers")
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("SELECT * FROM cost_reservations WHERE reservation_id=?",(reservation_id,)).fetchone()
        if row is None: raise ValueError("unknown reservation")
        if row["state"]=="settled":
            if row["charged_cents"]==charge and row["source"]==source:
                db.commit();return snapshot(db,row["run_id"])
            raise ValueError("already reconciled; use explicit adjustment workflow")
        if row["state"]=="released":
            raise ValueError("cannot settle released reservation")
        db.execute("""UPDATE cost_reservations SET state='settled',charged_cents=?,source=?,
          input_tokens=?,output_tokens=?,updated_at=? WHERE reservation_id=?""",
          (charge,source,input_tokens,output_tokens,utcnow(),reservation_id))
        if charge>row["reserved_cents"]:
            incident(db,row["run_id"],"critical","reservation_overrun",
                     {"reservation_id":reservation_id,"reserved_cents":row["reserved_cents"],"charged_cents":charge})
        state=snapshot(db,row["run_id"])
        if state["over_budget"]:
            incident(db,row["run_id"],"critical","run_budget_exceeded",state)
        db.commit()
        return state
    except Exception:
        db.rollback();raise

def mark_uncertain(db,reservation_id,reason):
    if not reason: raise ValueError("reason required")
    with db:
        row=db.execute("SELECT run_id,state FROM cost_reservations WHERE reservation_id=?",(reservation_id,)).fetchone()
        if row is None or row["state"] not in ("reserved","uncertain"): raise ValueError("invalid reservation state")
        db.execute("UPDATE cost_reservations SET state='uncertain',updated_at=? WHERE reservation_id=?",(utcnow(),reservation_id))
        incident(db,row["run_id"],"warning","unverified_usage",{"reservation_id":reservation_id,"reason":reason})

def release(db,reservation_id,reason):
    """Only legal when a caller confirms no billable request was made."""
    if not reason: raise ValueError("release reason required")
    with db:
        row=db.execute("SELECT state FROM cost_reservations WHERE reservation_id=?",(reservation_id,)).fetchone()
        if not row or row["state"]!="reserved": raise ValueError("cannot release an active/unknown/settled charge")
        db.execute("UPDATE cost_reservations SET state='released',updated_at=? WHERE reservation_id=?",(utcnow(),reservation_id))

def incident(db,run_id,severity,code,context):
    db.execute("INSERT INTO cost_incidents(run_id,severity,code,context,created_at) VALUES(?,?,?,?,?)",
               (run_id,severity,code,json.dumps(context,sort_keys=True),utcnow()))

def advise(db,run_id):
    """Structured recommendations for coordinator/Codex; never authorizes a spend."""
    state=snapshot(db,run_id)
    findings=[]
    if state["over_budget"]:
        findings.append({"severity":"critical","action":"stop_new_paid_dispatch","reason":"budget exceeded"})
    elif state["available_cents"]<=state["limit_cents"]//5:
        findings.append({"severity":"warning","action":"conserve_remaining_budget","reason":"at or below 20% available"})
    unknown=db.execute("SELECT count(*) FROM cost_reservations WHERE run_id=? AND state='uncertain'",(run_id,)).fetchone()[0]
    if unknown:
        findings.append({"severity":"critical","action":"reconcile_before_resuming","reason":f"{unknown} unknown billable executions"})
    return {"budget":state,"recommendations":findings,"recipient":"coordinator; Codex on critical or final review"}

def public_receipt(db,run_id):
    report=advise(db,run_id)
    return {"run_id":run_id,"budget":report["budget"],"recommendations":report["recommendations"],
            "note":"Aggregated estimated/verified local ledger only; not an external provider invoice. No credentials."}
