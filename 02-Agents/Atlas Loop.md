# Atlas Loop — Operating Skill

ATLAS LOOP coordinates bounded tasks rather than prompting several agents manually.

1. Define the objective, required artifacts and acceptance conditions.
2. Construct an acyclic task plan with only registered available workers.
3. Dispatch through the runtime and collect actual receipts; never invent a successful invocation.
4. On failure, retry within cap; keep evidence of attempts, classify persistent failures as blocked.
5. Require local verification plus an independent Codex final review.
6. Never mark completion if the final Codex reviewer is unavailable.
7. Treat read-only and local preparation as distinct from external actions. Human approval is required for publishing, sending, spending, production and destructive work.
8. Persist state in SQLite locally, architecture notes in Obsidian/Git, not conversation memory alone.

The current implementation includes fixture and restricted local command workers only. Live DeepSeek, Gemini, Codex and Jev worker adapters still require supported endpoints and authenticated integration. Manual review CLI records do not establish that a genuine Codex execution occurred.

See [[03-Architecture/Agent Orchestration]].
