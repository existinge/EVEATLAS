# BL Engine — private continuity bridge

This public repository contains reusable logic only. Do NOT commit any personal WATCH workbook, user ratings, aliases, feedback, or normalized private JSON here. The canonical source remains in the user's private ChatGPT Library.

## Executable local adapter

The offline, dependency-free tools/bl_continuity.py accepts private state JSON with watch, aliases, manual_overrides, explicit_deltas, and optionally r77_research_only. It produces a candidate audit. It is not a research crawler, MCP server or hosted database.

Command:

    python tools/bl_continuity.py --state /private/bl_engine_state.json --candidates /private/researched_candidates.json --output /private/novelty_audit.json
    python -m unittest discover -s tests -p 'test_bl_continuity.py' -v

An optional --feedback file takes explicit title/status decisions, processed only in-memory. The adapter does not persist changes. Persistence is a separate authorized, versioned private Library upload and read-back.

## Privacy and status integrity

- All WATCH and Manual Override titles block fresh classification regardless of status.
- Alias/homonym collisions fail closed. Do not merge unrelated productions.
- Similar names require identity review.
- Research-only candidates with no user decision never become Maybe/Investigate votes.
- Seen is not equivalent to completed; missing ratings are not invented.
- Canonical-source-completeness can only be declared after full WATCH, aliases, research and rejection sources were reconciled.
- NOVEL_CANDIDATE means no detected title collision; it does not independently prove legitimate story, good ending or source availability.

## Long-term architecture

1. Plugin skill holds user-tuned operating rules and interactive UI continuity across chats.
2. Private ChatGPT Library holds full versioned canonical checkpoints and feedback overlays.
3. Public EVEATLAS holds only portable code, tests and privacy-safe integration documentation.
4. A future authenticated MCP service may implement get_state, run_discovery, apply_feedback and export. None is deployed by this patch.

Always load the private canonical checkpoint first. Do not treat research handoff files or chat summaries as a complete WATCH source.
