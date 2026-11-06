# EVECLAW / OpenClaw host move — Windows to MacBook
Date: 2026-10-17
Status: PLANNED — not begun or confirmed completed
Affected: EVECLAW voice gateway, optional OpenClaw local host, ATLAS integrations
Related: [[08-Research/TYGER Full-Duplex Speech Controller - Scholar Handoff]]

## Decision / intent
User intends to stop hosting OpenClaw on the Windows gaming PC because the local services have been bloating resource usage and degrading performance. MacBook is the future preferred OpenClaw host. No change is authorized or performed yet. Do not run new voice-controller workloads on Windows.

## Proposed migration checklist — future, only when user is ready
- Inventory Windows OpenClaw gateway version/config, scheduled services, plugins, model provider routes, voice/TTS, Mem0 persistence, workflow state and logs. Record what is actually running.
- Discover MacBook model/architecture, RAM, storage, macOS, idle/sleep and power/network constraints; verify headless persistence feasibility.
- Back up and verify restore for OpenClaw configuration, persistent data and local Mem0 state. Transfer secrets through a secure channel; NEVER commit tokens, voice IDs, personal memories or raw configs to public EVEATLAS.
- Install/test Mac host in parallel without duplicated automated jobs, actions or receipts. Confirm model failovers, gateway reachability/authentication, ElevenLabs and voice, Mem0, ATLAS LOOP handoffs, monitoring and restart recovery.
- Cut over intentionally: disable Windows OpenClaw startup tasks/gateway once Mac host is proven. Confirm Windows idle resource usage improves and no orphan services remain.
- Keep rollback plan and document actual dates/evidence. Mac sleep, power and networking may affect always-on use.

## Architecture boundary
ATLAS LOOP is the canonical mutable state/scheduler/approval owner, while OpenClaw is task transport and local interaction as described by [[02-Agents/EveClaw Executive Mediation]]. Hosting relocation must not move cloud-runtime authority to a MacBook or introduce single-host hard dependency.

## Scholar implications
All future voice-system proposals including TYGER use MacBook as target. Benchmark on actual Mac hardware first; no RTX/CUDA extrapolation. Treat migration as an open dependency and distinguish planned from delivered in reports.

## Patch note / handoff
Macro: upcoming local host platform relocation Windows -> MacBook, motivated by preserving gaming performance.
Micro: voice-controller research deferred until post-migration hardware and compatibility verification.
Validation: documentation-only. No tests, migration or services changed.
