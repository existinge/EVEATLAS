# Architecture

Japanese Splat City is a browser game built with **Vite + TypeScript + Three.js**.
It runs a first-person explore-and-learn loop: the player walks a Japanese
shopping street, targets objects (E key), receives Japanese vocabulary, and
completes small missions.

## Module layout

```
src/
  main.ts                 Bootstrap: creates Game, wires HUD, fatal-error overlay
  engine/
    Game.ts               Composition root: renderer, scene, camera, main loop
    SceneManager.ts       Scene graph, sky, fog, lights, disposal
    AssetManager.ts       Texture / splat / audio loading with cache
    InputManager.ts       Keyboard + mouse state, pointer lock, event feed
    PlayerController.ts   WASD movement, mouse look, sprint, jump, gravity
    CollisionManager.ts   AABB colliders, ground/gravity resolution, bounds
  rendering/
    SplatRenderer.ts      Gaussian splat viewer (visual layer only)
    Environment.ts        Street lighting, ambient mood, sky dome
    GraphicsSettings.ts   Quality settings (pixel ratio, shadows, splat detail)
  world/
    ShoppingStreet.ts     Street layout: road, sidewalks, buildings, fences
    ConvenienceStore.ts   Convenience-store storefront and interior props
    Cafe.ts               Café storefront and seating
    InteractableObjects.ts Registry of props (vending machines, signs, ...)
  systems/
    InteractionSystem.ts  Raycast targeting, E interaction, contextual UI
    MissionSystem.ts      Mission state machines (3 missions)
    LearningSystem.ts     Vocabulary discovery, notebook state
    ProgressSystem.ts     localStorage persistence + reset
    AudioSystem.ts        Speech synthesis and UI sounds
  content/
    vocabulary.ts         Vocabulary schema + N4/N3 entries
    missions.ts           Mission definitions and dialogues
    dialogue.ts          Store/café NPC dialogue trees
  ui/
    HUD.ts               Reticle, hints, top bar, mission tracker
    InteractionPanel.ts  Targeted-object panel (Japanese first)
    MissionTracker.ts    Active mission HUD block
    VocabularyNotebook.ts Modal notebook (discovered words, readings)
    SettingsMenu.ts      Pause/settings modal
  types/
    game.ts              Shared types (vocabulary, mission, progress, ...)
tests/                    Vitest suites: missions, interactions, progress, smoke
```

## Key invariants

- **Visual vs. collision separation**: Gaussian splat content and street props
  are visual-only; movement collision comes exclusively from
  `CollisionManager` AABBs and ground height, never from splat data.
- **Milestones compose**: M1 movement, M2 splats, M3 environment, M4
  interaction, M5 learning, M6 missions, M7 persistence all plug into
  `Game`; each milestone keeps earlier gates working.
- **Content is data**: vocabulary, missions and dialogues live in `src/content`
  as typed data so they can be validated by tests and extended without engine
  changes.
- **Progress is local**: all persistence uses `localStorage` under a single
  namespaced key with a schema version and a reset-progress option.
