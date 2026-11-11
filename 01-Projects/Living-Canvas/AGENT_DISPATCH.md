# Agent dispatch — reusable single-ticket instruction

Use this **short dispatch** with your coding agent. Do not paste the whole pack into every turn.

~~~text
Repository: https://github.com/existinge/EVEATLAS
Project: 01-Projects/Living-Canvas
Entry: 01-Projects/Living-Canvas/START_HERE.md

Read root AGENTS.md and the project's START_HERE, ARCHITECTURE, PROTOCOL, GATES, and tickets/INDEX. Then select ONLY the next uncompleted ticket. First ticket is T00-PREFLIGHT. Keep all changes on a scoped feature branch and do not merge or deploy.

You must preserve the shared-space architecture, provider portability, deterministic coordinator, replaceable decider, and non-blocking living canvas. Do not convert this into a chat-turn drawing app, a computer-use click demo, or a canned lesson. No extra agents/services without a measured need.

Before coding, write one-paragraph understanding, exact files to change, acceptance test and stop condition. Execute the ticket, run real tests, attach evidence, then STOP with an Atlas handoff: branch/commit, changed files, pass/fail, actual vs simulated, known latency, blockers, next cursor.
~~~

When continuing an incomplete ticket, ask the agent to inspect the last handoff and current Git diff before modifying files. Treat the Git repo as authority over chat recollection.
