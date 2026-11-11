# Visual runtime — drawing without blocking on inference

## What actually draws
tldraw is a programmable canvas, not a visual model. It stores and renders objects (shapes, labels, arrows, positions) efficiently. React and Motion can animate visual properties and SVG paths. The fast model does NOT paint pixels: it selects constrained actions or numeric parameters. The deterministic renderer computes geometry and frames.

## Visual recipe contract
An approved concept can have a declarative recipe with:
- recipeId; stable semantic concept IDs
- primitives: text, path, node, edge, imageReference, chart, layout group
- object IDs (stable across updates)
- numeric controls: revealProgress 0..1, attention 0..1, layoutWeight 0..1, nodeCount integer within bounds
- allowed transforms and animation hints; accessible labels
- ownership/reversibility; semantic provenance and confidence presentation
- fallback if a recipe isn't present (neutral text/card, NEVER a falsely grounded picture)

The planner may suggest a new recipe asynchronously; a validator must constrain elements and geometry before committing it. The decider can operate numeric controls, within bounds, on an approved recipe. Computer-use clicking and arbitrary generated SVG scripts are not part of the hot path.

## Level of agency
L0: renderer-only math: deterministic layout, path interpolation, easing, camera.
L1: decider picks approved targets/parameters. Example: emphasize concept B; raise revealProgress to 0.6; shift focus to node #3.
L2: planner creates/changes semantic recipe/graph through validated schema.
L3: optional asset creation (SVG/icon/illustration) prepared asynchronously, subject to validation/attribution. Not required for first demonstration.

## Important distinction
"Transform 木 into a tree" requires a visual representation: SVG, stored procedural recipe, or a planner-generated recipe. tldraw alone does not invent tree geometry. Do NOT promise novel photorealistic or meaningful morphs merely because tldraw can animate.

## Control separation
Semantic transitions (change meaning/topic) require planner-approved states.
Stylistic transitions (position, opacity, highlight, layout) may be fast-decider-led when within current policy.
Speculative display should be a clearly non-assertive ghost/preview layer, timed to expire or reverse on correction.
A completed verbal correction supersedes stale provisional visual transitions.

## Rendering stack decision
For the first build: TypeScript + React + tldraw. Add Motion only when actual transition requirements exceed basic CSS/SVG animation. Rive is optional for elaborate prepared character motion; do not add in v0.1. No image model required to prove the pipeline.
Use tldraw's programmable Editor API directly if the Agent Starter Kit's chat-centric model loop would create blocking latency.

## Accessibility
Text alternatives; color is not the only stoplight signal; reduced-motion option; captions availability depends on voice provider; avoid overwhelming learners with simultaneous corrections and pictures.
