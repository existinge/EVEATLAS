# Japanese Splat City v3
Status: governed reboot — not yet proven playable.

**Canonical product vision:** [PRODUCT_CHARTER.md](./PRODUCT_CHARTER.md). JPSv3 serves Japanese learners across levels and must surpass the photography/vocabulary loop demonstrated by Shashingo through agency, contextual language use and meaningful interactions. No assumptions based on a founder's personal proficiency.

**Technology:** strict TypeScript + Vite + Three.js + Rapier, Spark splat renderer once the core game works; optional minimal React HUD, Playwright browser verification. Splats are presentation; meshes/colliders are gameplay. No required live LLM for the first complete loop.

**Builder:** DeepSeek Flash, governed by [AGENT_CONTRACT.md](./AGENT_CONTRACT.md). **Supervisor:** Antigravity watchdog per [SUPERVISOR.md](./SUPERVISOR.md). **Optional skills:** curated in [RESOURCES.md](./RESOURCES.md). Root Atlas AGENTS.md applies.

**Priorities:** M0 playable movement/collision/input -> M1 exploratory interactive Japanese scene and contextual branching errand -> M2 splat/polish without regressions -> M3 adaptation/content. Every milestone requires a runnable demo and tests. Avoid docs-only deliverables.
