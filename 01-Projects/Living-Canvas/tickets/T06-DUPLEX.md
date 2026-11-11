# T06 — Real duplex voice provider adapter

Timebox: 40–60 minutes (may require credentials/consent). Status: NOT STARTED. Depends on: T05/P5.

## Build
Use one real provider's supported developer session interface. It is the LIVE voice conversational partner. Add provider capability negotiation and an observation adapter for timed partial/final transcript, interruptions and speaker turns WHEN supported. Keep media transport swappable (native session SDK vs optional LiveKit); avoid rebuilding duplex from STT → text LLM → TTS unless explicitly chosen as fallback and labelled non-duplex.

No secret keys in Atlas public repo. Never use consumer voice app automation as though it exposes developer events.

## Gate P6
Real voice goes both ways; human interruption has observable effect; canvas receives authorized observation-based events; logs separate mic→transcript, decider, commit and paint timings. If partial transcript unavailable, report the actual limitation and demonstrate safe fallback, not a fake live semantic reaction.

## Forbidden
Building new speech model, hardcoding a paid provider as required, publishing private audio, claiming real-time from scripted inputs.

## Stop
Deliver provider capability report, usage cost, missing events, latency traces and T07 readiness.
