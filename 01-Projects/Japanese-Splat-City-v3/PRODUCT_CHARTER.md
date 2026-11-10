# Japanese Splat City v3 — Product Charter (2026-11-10)
**State:** reboot governed; no playable implementation verified. **Audience:** Japanese learners of varied proficiency, interests and accessibility needs. NEVER personalize the product baseline around the founder's language level.

## Product thesis
Shashingo is a reference for enjoyable Japanese place-based discovery, photos, vocabulary collection, listening and a review album. JPSv3 must exceed an object-label/photo-flashcard loop: use language as a means to perceive, explore, decide, cooperate, carry out errands, solve situated problems, and build understanding. Do not copy Shashingo's art, code, branding, assets or level layout.

The intended product is a **game first and learning environment always**, not a disguised quiz or a generic chatbot in a 3D scene. Japanese immersion must be compelling even when the player is not actively studying. The same world should support beginners through advanced learners via adjustable scaffolding, meaningful choice and optional complexity. CEFR/JLPT is reference metadata, not a hard gate or a user-specific target.

## Design pillars
1. **World before worksheets:** walkable, atmospheric, coherent Japanese neighborhood, camera/observation as one optional discovery instrument, believable environmental text/signs and contextual audio.
2. **Agency and consequences:** interactions matter; missions use reading/listening/decision-making, with alternate routes and recoverable misunderstandings. Never soft-lock because of a language error.
3. **Multidimensional language:** objects, verbs, spatial relations, grammar in context, pragmatic intent, conversation/listening and cultural nuance. No claim that one noun photographed equals competence.
4. **Adaptation without assumptions:** selectable help (translation on demand, kana/furigana/romaji preference, audio replay, speed, hints), optional challenge, and separate reading/listening/meaning competencies. Do not infer ability from nationality or preselect a founder-level curriculum.
5. **Pedagogical evidence:** track exposure separately from recognition and successful contextual use; spaced retrieval is optional and tied to prior encounters. Require actual evidence before claiming proficiency.
6. **Splat/mesh hybrid:** splats are scene presentation; meshes, colliders and explicit interaction markers deliver reliable gameplay. World must be playable with mesh fallback before splat integration.
7. **Access and feel:** responsive pointer lock/focus management, keyboard/mouse and extensible controller mapping, readable Japanese, pause, accessibility and graceful degraded graphics.

## Engine decision
Strict TypeScript, Vite, Three.js, Spark where compatible, Rapier, minimal React UI (optional), Playwright. Assets require provenance/license; deterministic local authored mission must run offline without LLM. Experimental OhMyGame/67.js and external skills are optional isolated workers, not runtime dependencies.

## First playable slice: Neighborhood Discovery Loop
One small street corner, an accessible shop interior, 5–8 inspectable environmental elements, one photograph/observation interaction, a scene journal, a lightweight configurable language support panel, and a *meaningful* contextual errand. Example: an NPC requests a drink and directions via short Japanese dialogue, player uses the shop signage and objects to decide how to respond, then receives consequence-driven feedback. This is an illustrative vertical-slice scenario, not a mandated hard-coded curriculum. The player can freely explore; mission should branch or give recovery hints and never require exposure to every flashcard first.

## MVP success criteria
From clean checkout: launch browser game, enter/exit input capture reliably, move and collide, observe and inspect, encounter Japanese text/audio with help options, complete contextual quest with meaningful alternate outcomes, save and reload, no critical console errors; unit + browser smoke tests and screenshots/traces; independent supervisor review. A polished screenshot without playable input is failure.

## Delivery
M0: working scene + first-person controls + collision + Playwright smoke, no splat prerequisite.
M1: environment exploration + observer/journal + multilingual scaffolding settings + meaningful quest + save.
M2: licensed splat integration + perf/fallback + sound/polish, without changing gameplay contracts.
M3: deeper adaptive language models and additional content based on demonstrated playability.
Do not confuse implementation status with design intent. ATLAS project governance lives here; game implementation should have a separate workspace/repository and PRs.
