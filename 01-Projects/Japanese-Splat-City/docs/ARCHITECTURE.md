# Architecture

Japanese Splat City is a browser game built with **Vite + TypeScript + Three.js**.
It runs a first-person explore-and-learn loop: the player walks a Japanese
shopping street, targets objects (E key), receives Japanese vocabulary, and
opens the notebook (N key). Milestone status and future work live in
[PLAN.md](PLAN.md); this file describes only what exists in `src/` today.

## Module layout (as built, 2026-11-09)

```
src/
  main.ts                 Bootstrap: creates Game, wires fatal-error overlay
  engine/
    Game.ts               Composition root: renderer, scene, camera, main loop,
                          splat viewer wiring (queueSplatScene), interaction +
                          learning wiring, pause/pointer-lock orchestration
    SceneManager.ts       Scene graph, sky, fog, lights, disposal
    InputController.ts    Keyboard + mouse state, pointer lock, E edge-trigger,
                          consumeInteract()
    PlayerController.ts   WASD movement, mouse look, sprint, jump, gravity,
                          axis-separated AABB collision resolution
  interaction/
    Interaction.ts        Pure math: rayAabb3 slab ray/AABB, interactionTarget()
    InteractiveRegistry.ts Registration, per-def 1.2 s cooldown, 12-entry history
  systems/
    LearningSystem.ts     Vocabulary discovery: encounter counts, fresh-word
                          events, snapshot/restore (versioned schema); no DOM,
                          no localStorage (M7 owns persistence)
  world/
    ShoppingStreet.ts     Street layout: road, sidewalks, 8 building boxes,
                          STREET_LAMPS registry + buildLamps() lighting,
                          STREET_PROPS + monument/prop transforms
    Colliders.ts          buildStreetWorld(): building + monument AABBs,
                          Colliders.poles (lamp poles, real colliders)
    Interactives.ts       12 InteractiveDefs (8 shopfront slabs from
                          BUILDING_BASES + monument + 3 props) — the shared
                          M4→M5 vocabulary contract
  content/
    vocabulary.ts         VocabularyEntry schema + 24 N4/N3 words, two per
                          interactable; pure data
  ui/
    MenuOverlay.ts        Play/pause + quality presets + control list
    InteractionHud.ts     Reticle, contextual Japanese prompt/message,
                          discovery toast
    VocabularyNotebook.ts Notebook overlay: N4/N3 sections, masked ？？？ rows
  types/
    gaussian-splats-3d.d.ts Ambient typing for the splat viewer
  styles/main.css         HUD, overlays, notebook styling
tests/                    Vitest suites: smoke, player, street-props,
                          lamp-colorization, interaction, learning
```

## Key invariants

- **Visual vs. collision separation**: Gaussian splat content and street props
  are visual-only; movement collision comes exclusively from AABBs built by
  `world/Colliders.ts` (buildings, monument footprint, lamp poles) resolved in
  `PlayerController`, never from splat data.
- **Milestones compose**: M1 movement, M2 splats, M3 props, M3.1 lighting, M4
  interaction, M5 learning all plug into `Game`; each milestone keeps earlier
  gates working. M6 missions and M7 persistence are staged in
  [PLAN.md](PLAN.md), not yet present in `src/`.
- **Content is data**: vocabulary lives in `src/content/vocabulary.ts` as typed
  data so it can be validated by tests and extended without engine changes;
  `world/Interactives.ts` is the single interaction registry (no second one).
- **One interaction + data hook**: the E path resolves the same `InteractiveDef`
  it shows, and `recordEncounter()` consumes its id — no parallel registries.
- **Persistence is deferred**: `LearningSystem` snapshot/restore is versioned
  and schema-checked, but nothing writes `localStorage` yet; M7 owns that.

## Planned modules (not in the tree — see PLAN.md staging)

`systems/MissionSystem.ts`, `systems/ProgressSystem.ts`,
`systems/AudioSystem.ts`, `content/missions.ts`, `content/dialogue.ts`,
`ui/MissionTracker.ts`, plus possible `world/ConvenienceStore.ts` / `Cafe.ts`
zone work. These names come from the original pre-M0 architecture sketch and
are subject to the as-built shapes (e.g. collision stayed in
`PlayerController`, the splat viewer stayed wired in `Game.ts`).
