#!/usr/bin/env python3
"""EVEATLAS Signal Desk: offline, evidence-first research ingestion.

No network calls, scraping, AI API calls, publishing, or autonomous scheduling.
Feed JSON records obtained by an approved connector or human researcher.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "private" / "signal-desk.sqlite3"
DEFAULT_OUTPUT = ROOT / "private" / "signal-desk-runs"
DECISIONS = {"usable_as_written", "usable_with_narrower_wording", "blocked_until_checked"}
STATES = {"needs_review", "cleared", "blocked"}
REQUIRED = {"claim", "source_url", "published_date", "source_type", "evidence", "decision", "status"}
SOURCE_TYPES = {"official_announcement", "official_docs", "independent_report", "user_report", "opinion"}
MAX_INPUT_BYTES = 2_000_000

def canonical_url(raw):
    if not isinstance(raw, str):
        raise ValueError("source_url must be a string")
    parts = urlsplit(raw.strip())
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("source_url must be a public HTTPS URL without credentials")
    if parts.hostname.lower() in {"localhost", "127.0.0.1", "::1"} or parts.hostname.endswith(".local"):
        raise ValueError("local URLs are not allowed")
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid", "ref_src"}]
    return urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/") or "/", urlencode(kept), ""))

def event_id(record):
    if record.get("event_id"):
        val = record["event_id"]
        if not isinstance(val, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}", val):
            raise ValueError("event_id must be an ASCII slug (1-120 chars)")
        return val
    url = canonical_url(record["source_url"])
    xmatch = re.search(r"/status/(\d+)", url)
    key = "x:" + xmatch.group(1) if xmatch else url
    return hashlib.sha256(key.encode()).hexdigest()[:20]

def validate(record):
    if not isinstance(record, dict):
        raise ValueError("each record must be an object")
    missing = REQUIRED - record.keys()
    if missing:
        raise ValueError("missing: " + ", ".join(sorted(missing)))
    for field in ("claim", "evidence", "published_date", "source_type", "status", "decision"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"{field} must be a nonempty string")
    for field in ("claim", "evidence"):
        if len(record[field]) > 6000:
            raise ValueError(f"{field} exceeds length limit")
    if record["source_type"] not in SOURCE_TYPES:
        raise ValueError("invalid source_type")
    if record["decision"] not in DECISIONS or record["status"] not in STATES:
        raise ValueError("invalid decision/status")
    try:
        date = dt.date.fromisoformat(record["published_date"])
    except ValueError as exc:
        raise ValueError("published_date must be YYYY-MM-DD") from exc
    if date > dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1):
        raise ValueError("publication date cannot be in the distant future")
    if record["status"] == "cleared" and record["decision"] == "blocked_until_checked":
        raise ValueError("blocked decision cannot be cleared")
    if record["status"] == "cleared" and not record.get("reviewed_by"):
        raise ValueError("cleared records require reviewed_by")
    url = canonical_url(record["source_url"])
    for field in ("supporting_url",):
        if record.get(field):
            canonical_url(record[field])
    normalized = dict(record)
    normalized["source_url"] = url
    normalized["event_id"] = event_id(record)
    return normalized

def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS findings (event_id TEXT PRIMARY KEY, source_url TEXT NOT NULL, status TEXT NOT NULL, decision TEXT NOT NULL, covered_at TEXT, data_json TEXT NOT NULL, updated_at TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS receipts (run_id TEXT PRIMARY KEY, result TEXT NOT NULL, candidate_count INTEGER NOT NULL, accepted_count INTEGER NOT NULL, generated_at TEXT NOT NULL)")
    return db

def ingest(db, records, max_candidates=8):
    if not isinstance(records, list) or len(records) > max_candidates:
        raise ValueError(f"input must be a list with at most {max_candidates} records")
    prepared = [validate(record) for record in records]  # fail atomically on invalid input
    ids = [r["event_id"] for r in prepared]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate event_id within the same run")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    accepted, skipped = [], []
    with db:
        for record in prepared:
            old = db.execute("SELECT data_json, covered_at FROM findings WHERE event_id=?", (record["event_id"],)).fetchone()
            if old and old[1] and not record.get("material_update", False):
                skipped.append(record["event_id"])
                continue
            if old and old[1] and record.get("material_update", False) and not record.get("update_reason"):
                raise ValueError("material_update requires update_reason")
            db.execute("INSERT INTO findings(event_id,source_url,status,decision,covered_at,data_json,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET source_url=excluded.source_url,status=excluded.status,decision=excluded.decision,data_json=excluded.data_json,updated_at=excluded.updated_at",
                       (record["event_id"], record["source_url"], record["status"], record["decision"], old[1] if old else None, json.dumps(record, ensure_ascii=False), now))
            accepted.append(record)
    return accepted, skipped

def render_brief(records, max_findings=3):
    eligible = [r for r in records if r["status"] == "cleared" and r["decision"] != "blocked_until_checked"]
    lines = ["# ATLAS Signal Desk — Research Brief", "", f"Generated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}", "",
             "Only human-reviewed records marked cleared appear here. Original sources still determine current truth.", ""]
    for record in eligible[:max_findings]:
        lines += [f"## {record['claim']}", "", f"Source: {record['source_url']}",
                  f"Published: {record['published_date']} · Type: {record['source_type']}",
                  f"Review: {record['decision']} by {record['reviewed_by']}", "",
                  "Evidence:", record["evidence"], "",
                  "Practical use (proposed, not verified):", record.get("practical_use", "Not evaluated"), "",
                  "Limits / uncertainty:", record.get("caveat", "Not independently tested"), "",
                  "Decision: " + record.get("recommendation", "watch"), ""]
    if not eligible:
        lines.append("No cleared findings this run. Pending or blocked evidence is not a positive finding.")
    return "\n".join(lines) + "\n", eligible[:max_findings]

def run(input_path, db_path, output_dir, max_candidates=8, max_findings=3):
    source = Path(input_path)
    if source.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("input too large")
    records = json.loads(source.read_text(encoding="utf-8"))
    db = connect(db_path)
    try:
        accepted, skipped = ingest(db, records, max_candidates)
        brief, selected = render_brief(accepted, max_findings)
        now = dt.datetime.now(dt.timezone.utc)
        run_id = now.strftime("%Y%m%dT%H%M%S%fZ")
        output = Path(output_dir) / run_id
        output.mkdir(parents=True, exist_ok=False)
        (output / "brief.md").write_text(brief, encoding="utf-8")
        (output / "evidence.json").write_text(json.dumps(accepted, indent=2, ensure_ascii=False), encoding="utf-8")
        receipt = {"run_id":run_id, "input_count":len(records), "accepted_count":len(accepted),
                   "brief_count":len(selected), "skipped_previously_covered":skipped,
                   "pending_count":sum(r["status"] != "cleared" for r in accepted),
                   "result":"completed_local_ingestion", "external_actions":0, "model_calls":0}
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        with db:
            for r in selected:
                db.execute("UPDATE findings SET covered_at=? WHERE event_id=?", (now.isoformat(), r["event_id"]))
            db.execute("INSERT INTO receipts VALUES (?,?,?,?,?)",
                       (run_id, receipt["result"], len(records), len(accepted), now.isoformat()))
        return output, receipt
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON array of supplied candidate evidence records")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--max-findings", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.max_candidates <= 100 or not 1 <= args.max_findings <= 20:
        parser.error("candidate and finding limits must be positive and bounded")
    try:
        output, receipt = run(args.input, args.db, args.output, args.max_candidates, args.max_findings)
        print(json.dumps({"path":str(output), **receipt}, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"Signal Desk failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
