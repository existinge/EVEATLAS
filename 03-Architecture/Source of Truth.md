# Source of Truth

- Obsidian Markdown: canonical plans, business hypotheses, evidence summaries, decisions and desired project state.
- GitHub: version history and collaboration; PRs and CI protect reviewed state.
- Runtime/repository tests and telemetry: evidence of actual working software and live product status.
- Private bookkeeping/payment processor: detailed transactional financial truth; only safe aggregate summaries in public vault.
- Agent memory: temporary retrieval/cache, not authority to silently overwrite canonical files.

## Sync
Clone existinge/EVEATLAS locally and open folder as an Obsidian vault. Pull before editing, use scoped feature branches for agent changes, inspect diffs, run tests, open PR and resolve conflicts manually. Avoid duplicate canonical notes.

## Decision rights
Researcher drafts findings, builder proposes implementation, independent reviewer evaluates, human authorizes public, commercial and high-risk actions. Record decisions in [[05-Decisions/Decision Log]].