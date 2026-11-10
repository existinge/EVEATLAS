# Shashingo: Learn Japanese with Photography — comparative research

**Created:** 2026-11-10 12:26 (local, UTC-05:00)
**Fetched via:** `web_fetch` (HTTP 200) on the Steam store page on 2026-11-10.
**Status:** Evidence note for Japanese Splat City v3 (M1 design reference). Not a launch, review, or endorsement.

> **Tooling disclosure (honesty per EVEATLAS contract):** the harness `web_search` tool was
> unavailable during this research pass (DeepSeek endpoint returned HTTP 402 Insufficient
> Balance). All facts below therefore come from direct page fetches only, not from search
> snippets. One earlier fetch of a guessed app id returned an unrelated game (Steam app
> 2884670, "Premier Servi" — a French pastry game); that id was *disconfirmed* and the
> correct id **1632490** verified from the store URL structure. Treat review-count details
> as point-in-time snapshots.

## Source
- Steam store page: https://store.steampowered.com/app/1632490/Shashingo_Learn_Japanese_with_Photography/
  (fetched 2026-11-10; content reflected in summary below)

## Confirmed facts
| Field | Value |
|---|---|
| Steam App ID | **1632490** (not 2884670) |
| Full title | **Shashingo: Learn Japanese with Photography** |
| Developer / Publisher | **Autumn Pioneer** |
| Release date | **Feb 27, 2024** |
| Reviews | Very Positive; ~90% positive (~658 reviews at fetch time) |
| Genre / pitch | Virtual-photography edutainment: photograph fictional Japanese streets to capture new words as translated flashcards |
| Core loop | Explore scene → photograph objects → words captured into a flashcard collection for study |
| Languages | ~8 interface languages; **Japanese-only full audio** |

## Why this matters for Japanese Splat City v3
- Validates the core charter assumption: *contextual encounter → vocabulary capture → owned
  study collection* is a proven, commercially received loop in this niche.
- Shashingo's flashcard collection ≈ our **observation journal**; its photograph-trigger ≈ our
  **crosshair inspect + E** interaction; its scene-per-word ≈ our "language lives on scene
  objects" rule.
- Differentiation: jpsv3 is a freely walkable 3D neighborhood with physics + an NPC errand
  quest, rather than a fixed camera-photography puzzle; we add per-object **language-assist
  settings** (furigana / romaji / translation), which Shashingo does not headline.

## Disconfirming / open notes
- We have **no** confirmed source for Shashingo's internal difficulty curve, per-object
  flashcard metadata, or localization details beyond the store blurb; do not cite specifics
  we did not fetch.
- Full-audio-in-Japanese-only is a notable precedent for putting the target language first in
  audio, while keeping UI language-agnostic — mirrors our bilingual text-first approach.

## Decisions influenced (proposed, see PRODUCT_CHARTER / 05-Decisions)
1. M1 observation journal persists vocabulary entries with per-entry assist flags.
2. Errand quest should drive the player to *re-encounter* words already journaled
   (recovery through context), echoing flashcard repetition.