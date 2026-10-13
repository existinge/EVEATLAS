# ATLAS LOCAL AI NODE — AGENT HANDOFF PACKET

> **Copy and paste this entire block into any agent (Eve, OpenClaw, Codex, ChatGPT, or Python/TS script) that needs to utilize the MacBook Air M4 as a zero-cost local inference node.**

---

## 1. Node Identity & Role

- **Host Machine:** MacBook Air M4 (16 GB Unified Memory)
- **Node Role:** Cheap local generative worker + high-speed typed decider.
- **Cost:** $0 API spend.
- **ATLAS Tier:** Worker / Subordinate execution node.
- **Safety Boundary:** Local outputs are **DRAFT / ADVISORY** only. The local node CANNOT self-approve external outreach, spending, publishing, or irreversible operations. Critical outputs still require independent review (GPT/Codex-tier) before being marked DONE.

---

## 2. LAN Connection Details

- **LAN Base URL:** `http://192.168.1.249:11435`
- **Protocol:** HTTP (REST / JSON)
- **Health Check:** `GET http://192.168.1.249:11435/api/ps`
  - Expected loaded models: `lfm2.5:8b` and `tev1:0.8b` (both resident simultaneously).

---

## 3. Worker Capability: `lfm2.5:8b` (Generative & Tool Calling)

Use for: extraction, formatting, code drafting, document summarization, tool-call trial runs.

- **Model ID:** `lfm2.5:8b`
- **Architecture:** 8.5B MoE (~1B active parameters per token).
- **Measured Speed:** ~75 tokens/sec decode.
- **Context Length:** 8,192 tokens.
- **API Endpoint:** `POST http://192.168.1.249:11435/v1/chat/completions` (OpenAI-compatible) or `POST http://192.168.1.249:11435/api/chat`
- **Native Tool Calling:** Supported (OpenAI functions format).

> ⚠️ **MANDATORY INVARIANT FOR WORKER CALLS:**
> `lfm2.5:8b` performs internal reasoning by default and emits a `<think>` block before answering.
> **You MUST set `max_tokens` (or `num_predict`) to at least `1500`.**
> A small token limit (e.g. 100-300) will be consumed entirely by the thinking preamble, returning empty content.

### Worker Example (Python):
```python
import requests

response = requests.post(
    "http://192.168.1.249:11435/v1/chat/completions",
    json={
        "model": "lfm2.5:8b",
        "messages": [
            {"role": "system", "content": "You are a concise engineering assistant."},
            {"role": "user", "content": "Write a python regex to parse ISO 8601 timestamps."}
        ],
        "max_tokens": 1500,
        "temperature": 0.1
    },
    timeout=60
)
result = response.json()["choices"][0]["message"]["content"]
print(result)
```

### Worker Example with Tool Calling (cURL):
```bash
curl http://192.168.1.249:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lfm2.5:8b",
    "messages": [{"role": "user", "content": "Check the status of order 4921."}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "lookup_order",
        "description": "Fetch order details by ID",
        "parameters": {
          "type": "object",
          "properties": {"order_id": {"type": "string"}},
          "required": ["order_id"]
        }
      }
    }],
    "max_tokens": 1500
  }'
```

---

## 4. Decider Capability: `tev1:0.8b` (Typed Decisions / Jev-Compatible)

Use for: intent routing, support ticket triage, safety/policy gating, priority scoring, spam filtering.

- **Model ID:** `tev1:0.8b`
- **Architecture:** 752M parameter decision model (MLX backend).
- **Measured Latency:** ~130 ms.
- **Output:** Exact probabilities over closed label sets (**0 generated text tokens**, no markdown to parse, no hallucinated fields).
- **API Endpoint:** `POST http://192.168.1.249:11435/v1/systemone`
- **Question Types:**
  1. `choice` — single-select from predefined options (returns winning choice + probability distribution).
  2. `noul` — boolean proposition (returns calibrated true/false probability between 0.0 and 1.0).
  3. `score` — rubric ranking (returns expected level + distribution).
- **Batching:** Up to 64 questions can be asked about the same state in a single call.

### Decider Example (Python):
```python
import requests

payload = {
    "model": "tev1:0.8b",
    "state": "Customer email: Can you tell me if my refund for order #123 has cleared yet?",
    "questions": {
        "intent": {
            "type": "choice",
            "instructions": "What is the primary customer intent?",
            "criteria": {
                "refund_inquiry": "Asking about return or refund status",
                "tech_support": "Troubleshooting a broken product",
                "sales_question": "Pre-purchase inquiry"
            }
        },
        "is_urgent": {
            "type": "noul",
            "instructions": "Does this message express extreme urgency or anger?"
        }
    }
}

response = requests.post("http://192.168.1.249:11435/v1/systemone", json=payload, timeout=10)
answers = response.json()["answers"]

intent = answers["intent"]["choice"]
urgent_prob = answers["is_urgent"]["noul"]

print(f"Intent: {intent} (urgency prob: {urgent_prob:.2f})")
```

---

## 5. Troubleshooting & Fallback Rules

1. **If node connection drops or times out:**
   - Verify Mac is awake and connected to the same LAN (`ping 192.168.1.249`).
   - Query `http://192.168.1.249:11435/api/version`. If down, the Mac daemon may need restarting via `python3 local-node/localnode.py start`.
2. **If memory pressure occurs:**
   - The Mac runs an automatic background memory guard. If RAM pressure exceeds safe limits, the guard sheds the worker (`lfm2.5:8b`) first while keeping the lighter decider (`tev1:0.8b`) resident.
   - Run `python3 local-node/localnode.py ensure` on the Mac to restore resident state once pressure subsides.
3. **If `tev1:4b` higher accuracy is needed:**
   - The Mac also houses `tev1:4b` (4.2B, 100% classification accuracy on test sets). Target `"model": "tev1:4b"` if memory allows and precision outweighs latency.
