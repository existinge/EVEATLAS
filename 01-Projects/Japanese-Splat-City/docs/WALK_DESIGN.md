# WALK_DESIGN — Japanese Splat City, 60–90 m enclosed walkable block

Design intent for the acceptance scene (`Assets/Scenes/WalkMain.unity`), authored in
the editor once the license blocker lifts. Design is editor-independent; nothing here
is built yet. All lengths are Unity world units = meters.

## Layout (top-down, not to scale)

```
        ┌─────────────── N (street splat frontage continues past both ends)
        │   lit storefront (spawn faces it, see Spawn)
        │
   A ───┴───────────────┬───────────────┬───────────────┬─────────────── M
   │     bay 01         │     bay 02    │ … storefront bays (reusable) …
   │  (lit, open)       │  (shutter up) │
   │                    │               │
   │  /// arcade /// covered main street, 4 m wide, 60–90 m long ///        │
   │                    │               │
   │  service lane entrance (CONNECTION 1: gap at bay 06)        │
   │    ↙               │               │
   │  narrow lane 2.2 m bends 90° twice (service feel) ──► … Café windows │
   │                    │               │        │
   │                    │               │  CONNECTION 2 back into arcade  │
   │   vending nook     │               │        │
   │                    │               │        ▼
   M ───────────────────┴───────────────┴─────────── rejoin (awning + café) ┴ A
```

- Main arcade: straight, 4.0 m wide, 60–90 m long (length finalized in editor), partially
  covered with translucent canopy + alternating lighting poles (architectural splat refers).
- Service lane: 2.2 m wide corridor parallel/zig-zagging behind the arcade's street side,
  with a 90°–180° bend, connecting back into the arcade at exactly two points
  (CONNECTION 1 near the start, CONNECTION 2 at the rejoin). Loop + shortcut, no dead end.
- Spawn: player placed at the arcade end facing the first lit storefront (glowing sign,
  warm interior light), one splat anchor visible ahead through the arcade.
- Rejoin (second connection): produce awning (striped), vending machine nook with
  light spill, and café windows (lit) mark the return point.

## Dressing kit (reusable, authored once, instanced ~20–30×)

- Storefront bay: door aperture + recessed shop floor, variants: shutter up/down,
  lit/unlit, window stickers. Instanced along both arcade sides.
- Japanese signage: sign rail above each bay, hiragana/katakana/kanji textures
  (Japanese-font provenance recorded in `docs/ASSET_PROVENANCE.md`), vertical
  hanging signs at junctions.
- Canopy segments, vending machines, produce crates, lanterns, bicycle, drainpipes.

## Acceptable-ground-truth rules

- Floor / walls / interior colliders: Unity primitive/mesh colliders; player never
  leaves the enclosed volume (outward faces blocked).
- Occluder: opaque storefront boxes + lane walls are occluders; the Gaussian splat is
  Z-tested, so solid geometry occludes splat correctly (renderer README claim — verify
  empirically on first packaged run).
- One licensed street-splat anchor visible from the arcade (per `docs/SPLAT_PROCUREMENT.md`).

## Evidence capture plan (packaged player, offline)

Route: spawn → arcade walk → CONNECTION 1 → service lane bend → CONNECTION 2 rejoin
(produce awning / vending nook / café windows) → return to spawn. Four evidence frames:
`frame-spawn`, `frame-junction`, `frame-servicebend`, `frame-rejoin` via
`FpsAndCapture` waypoint callbacks (`native/Assets/Scripts/Tooling/FpsAndCapture.cs`).

Acceptance assertions recorded in `docs/TEST_REPORT.md`: offline launch, splat visible,
collision keeps player inside, loop is closed and both connections traversable,
60 fps @ 1080p provisional on RTX 2080 Ti (frame-time rows in packaged fps.csv).
