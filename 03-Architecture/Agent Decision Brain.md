# ATLAS Brain — Bounded Deterministic Decisions

**Status:** Rule-based routing/recovery functions implemented; live workers and cloud scheduler are **not** connected.

The routing brain checks capability fit, worker availability, per-task spending ceilings, and critical accounting incidents. It emits `route`, `hold` or `escalate`; this is a recommendation, **not** an execution permission or model API call.

Recovery advice returns `retry`, `switch_strategy`, `escalate` or `stop`. Consecutive identical failure signatures trigger strategy switching before exhausting expensive retries.

Treasurer maintains authoritative cost reservations. Brain must read Treasurer's currently available funds; the future live dispatch service must then atomically reserve capacity before every external model request. Codex remains the mandatory final technical reviewer and receives critical incident evidence.

This minimal layer deliberately uses no Jev, Gemini or DeepSeek inference. Benchmark optional probabilistic routing after live worker integrations are operational.

Tests: `python -m unittest discover -s tests -v`.
