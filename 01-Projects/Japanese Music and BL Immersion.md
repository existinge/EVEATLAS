# Japanese Immersion — Music and BL (experimental)

**Date:** 2026-10-18  
**Status:** Local metadata adapter committed on experimental branch; authentication, live retrieval, scheduled sync, and ChatGPT ingestion NOT connected or verified.

## Goal
Replace rote Japanese drills with daily curiosity about actual Japanese songs and BL scenes. Prioritize conversational N4→N3 practice, nuanced speech, and user-led roleplay. English is a rescue rail. Never treat inferred music language as confirmed. Avoid AI-created drama recommendations.

## Data flow
1. User authenticates `ytmusicapi` locally on MacBook. Keep browser headers/cookies outside the public repository, backups and chat.
2. Run `python tools/ytmusic_immersion.py --auth ~/.config/eveatlas/ytmusic/browser.json --output ~/ytmusic-immersion.json`.
3. Review the output (song titles, artists, video IDs, coarse played labels), select actual Japanese songs, and share only the metadata the user wants in the practice chat. This is a **manual** step until an approved ingestion connector is built.
4. Use a current song as conversation seed; ask user what lyric or emotion caught their attention. For copyrighted lyrics, quote only very short excerpts or ask the user to supply the excerpt for discussion; don't reproduce full lyrics.
5. Have the learner paraphrase in Japanese, respond as a BL character, or improvise a line. Recycle prior expressions naturally, not as a compulsory quiz.
6. Record only lightweight progress notes if user approves: expressions practiced, comprehension gaps, preferred formats. Do not commit personal listening history or private progress to this public repo.

## Session recipe (10–15 min)
- **Hook:** One actually listened-to Japanese track or a BL scene the user names.
- **Notice:** One phrase, nuance, or grammar structure relevant to the scene.
- **Perform:** Two-turn roleplay or voice acting; user speaks first when possible.
- **Transfer:** Reuse the expression in a different situation.
- **Recall:** One natural callback to a previous expression.
- **Close:** Optional choice of what to explore next, never homework by default.

## Safety / implementation gates
- The adapter is **read-only** and calls `get_history()` only.
- `ytmusicapi` is unofficial; its history may be partial, and auth may stop working.
- No scraping lyrics in the sync job, no autonomous YouTube account mutations.
- Keep auth files and JSON exports off Git; do not place them in Google Drive unless explicitly authorized.
- Test with mocked history before enabling any automation; check handling of missing metadata and repeated songs.
- Later: user-approved local scheduler + privacy filter + opt-in delivery channel. A scheduled ChatGPT task cannot assume it can see local MacBook files.

## Handoff to Scholar / Atlas
Classify as experimental connector, not production. Evaluate API stability, metadata accuracy, auth exposure, and feasibility of securely ingesting a fresh snapshot into the chat. Maintain dated patch notes for changes to this pipeline.

## Patch note — 2026-10-18
Added `tools/ytmusic_immersion.py` on `feat/japanese-immersion-music-bridge`: a local, read-only listening-history snapshot exporter. No credentials, actual listening data, or automated schedule were added. Next steps: local MacBook authentication, mocked tests, end-to-end user validation, then optional scheduled sync.
