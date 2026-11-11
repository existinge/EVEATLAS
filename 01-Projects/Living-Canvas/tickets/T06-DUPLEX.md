# T06 — Real duplex voice provider adapter

Timebox: 40–60 minutes (may require credentials/consent). Status: NOT STARTED. Depends on: T05/P5.

## Build
Evaluate Gemini Live's native developer interface on a verified free tier first, per the [provider policy](../VOICE_AND_MODELS.md#provider-policy). Record model/version, date, account/region availability, quotas, session limits, data handling, and how paid fallback is disabled. Use synthetic or consented test audio. If no eligible free tier supports the required session, record P6 as blocked and retain offline replay. A paid experiment requires explicit opt-in and a cap.

Use one eligible provider's supported developer session interface. It is the LIVE voice conversational partner. Add provider capability negotiation and an observation adapter for timed partial/final transcript, interruptions and speaker turns WHEN supported. Keep media transport swappable (native session SDK vs optional LiveKit); avoid rebuilding duplex from STT → text LLM → TTS unless explicitly chosen as fallback and labelled non-duplex.

No secret keys in Atlas public repo. Never use consumer voice app automation as though it exposes developer events.

## Gate P6
Real voice goes both ways; human interruption has observable effect; canvas receives authorized observation-based events; logs separate mic→transcript, decider, commit and paint timings. If partial transcript unavailable, report the actual limitation and demonstrate safe fallback, not a fake live semantic reaction.

## Forbidden
Building new speech model, hardcoding a paid provider as required, publishing private audio, claiming real-time from scripted inputs.

## Stop
Deliver observed session and event capabilities, usage/cost evidence, missing events, latency traces and T07 readiness. Documentation and simulated events alone do not pass P6.
