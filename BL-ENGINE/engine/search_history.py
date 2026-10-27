"""Durable JSONL recording of attempted searches, including zero-result searches."""
import json
from datetime import datetime,timezone

def log_search(path, *, query, source, language, candidates, eligible):
    record={"timestamp":datetime.now(timezone.utc).isoformat(),"query":query,"source":source,"language":language,"candidate_count":candidates,"eligible_count":eligible}
    with open(path,"a",encoding="utf-8") as f:f.write(json.dumps(record,ensure_ascii=False)+"\n")
    return record
