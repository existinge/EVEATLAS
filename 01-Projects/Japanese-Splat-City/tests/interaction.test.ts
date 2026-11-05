/**
 * Milestone M4 — interaction core, registry and world integration tests.
 *
 * Three layers, mirroring the module layering:
 *  1. Pure ray/AABB math (`Interaction.ts`) — exact hit distances, misses,
 *     inside-origin, direction scale invariance, maxDistance gating.
 *  2. Registry behavior (`InteractiveRegistry.ts`) — cooldown, history cap,
 *     unknown-id rejection, target delegation.
 *  3. World data (`Interactives.ts`) — the 12 interactables form the M4→M5
 *     vocabulary contract (unique ids, Japanese labels, non-empty data) and
 *     every hotspot box is clear of the collision solids (buildings, lamp
 *     poles, monument plinth) so a player can always stand and reach it.
 *
 * All modules under test are renderer/DOM-free; no WebGL needed.
 */

import { describe, expect, it } from 'vitest';
import { rayAabb3, interactionTarget, type Aabb3 } from '../src/interaction/Interaction';
import { InteractiveRegistry } from '../src/interaction/InteractiveRegistry';
import { INTERACTABLES } from '../src/world/Interactives';
import {
  BUILDING_BASES,
  STREET,
  STREET_LAMPS,
  LAMP_POLE_HALF,
  MONUMENT,
  monumentFootprint,
} from '../src/world/ShoppingStreet';

/** Strict (open-interval) 3D overlap: touching faces are NOT an overlap. */
function overlaps(a: Aabb3, b: Aabb3): boolean {
  return (
    a.minX < b.maxX && a.maxX > b.minX &&
    a.minY < b.maxY && a.maxY > b.minY &&
    a.minZ < b.maxZ && a.maxZ > b.minZ
  );
}

// ---------------------------------------------------------------------------
// 1. Ray / AABB math
// ---------------------------------------------------------------------------

describe('rayAabb3', () => {
  const box: Aabb3 = { minX: -1, maxX: 1, minY: 0, maxY: 2, minZ: 4, maxZ: 6 };

  it('returns the entry distance for a straight hit', () => {
    expect(rayAabb3({ x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, box)).toBe(4);
  });

  it('is invariant to direction length', () => {
    expect(rayAabb3({ x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 100 }, box)).toBe(4);
    expect(rayAabb3({ x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 0.01 }, box)).toBe(4);
  });

  it('returns null for a sideways miss', () => {
    expect(rayAabb3({ x: 5, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, box)).toBeNull();
    expect(rayAabb3({ x: 0, y: 3, z: 0 }, { x: 0, y: 0, z: 1 }, box)).toBeNull();
  });

  it('returns null when the ray points away from the box', () => {
    expect(rayAabb3({ x: 0, y: 1, z: 10 }, { x: 0, y: 0, z: 1 }, box)).toBeNull();
  });

  it('returns 0 when the origin is inside the box', () => {
    expect(rayAabb3({ x: 0, y: 1, z: 5 }, { x: 0, y: 0, z: 1 }, box)).toBe(0);
  });

  it('honors maxDistance', () => {
    expect(rayAabb3({ x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, box, 3)).toBeNull();
    expect(rayAabb3({ x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, box, 4)).toBe(4);
  });

  it('rejects parallel rays outside the slab', () => {
    expect(rayAabb3({ x: 0, y: 1, z: 100 }, { x: 1, y: 0, z: 0 }, box)).toBeNull();
  });
});

describe('interactionTarget', () => {
  const near: Aabb3 = { minX: -1, maxX: 1, minY: 0, maxY: 2, minZ: 2, maxZ: 3 };
  const far: Aabb3 = { minX: -1, maxX: 1, minY: 0, maxY: 2, minZ: 8, maxZ: 9 };
  const defs = [
    { id: 'far', label: 'f', reading: 'f', description: 'f', message: 'f', action: 'f', box: far },
    { id: 'near', label: 'n', reading: 'n', description: 'n', message: 'n', action: 'n', box: near },
  ];

  it('picks the nearest hit regardless of definition order', () => {
    const hit = interactionTarget(defs, { x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, 20);
    expect(hit?.id).toBe('near');
  });

  it('returns null when nothing is within maxDistance', () => {
    // Nearest box entry is at t = 2; a reach of 1.5 must miss everything.
    expect(interactionTarget(defs, { x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, 1.5)).toBeNull();
  });

  it('returns the box when its entry sits exactly at maxDistance', () => {
    expect(interactionTarget(defs, { x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, 2)?.id).toBe('near');
  });

  it('returns null for an empty def list', () => {
    expect(interactionTarget([], { x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, 20)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 2. Registry behavior
// ---------------------------------------------------------------------------

describe('InteractiveRegistry', () => {
  const defs = [
    { id: 'a', label: 'あ', reading: 'あ', description: 'd', message: 'm', action: 'a', box: { minX: 0, maxX: 1, minY: 0, maxY: 1, minZ: 0, maxZ: 1 } },
    { id: 'b', label: 'い', reading: 'い', description: 'd', message: 'm', action: 'a', box: { minX: 0, maxX: 1, minY: 0, maxY: 1, minZ: 2, maxZ: 3 } },
  ];

  it('registers defs and resolves by id', () => {
    const r = new InteractiveRegistry(defs);
    expect(r.size).toBe(2);
    expect(r.get('a')?.label).toBe('あ');
    expect(r.get('nope')).toBeUndefined();
    expect(r.all()).toHaveLength(2);
  });

  it('rejects unknown ids and honors the cooldown per def', () => {
    const r = new InteractiveRegistry(defs, 10_000);
    expect(r.interact('nope')).toBeNull();
    expect(r.interact('a')).not.toBeNull();
    expect(r.interact('a')).toBeNull(); // still cooling down
    expect(r.interact('b')).not.toBeNull(); // other def unaffected
    expect(r.historySnapshot()).toHaveLength(2);
  });

  it('caps the history at historyLimit, most-recent first', () => {
    const r = new InteractiveRegistry(defs, 0, 2);
    r.interact('a');
    r.interact('b');
    r.interact('a');
    const history = r.historySnapshot();
    expect(history).toHaveLength(2);
    expect(history[0].id).toBe('a');
    expect(history[1].id).toBe('b');
  });

  it('returns history entries with the label/message snapshot', () => {
    const r = new InteractiveRegistry(defs, 0);
    const entry = r.interact('a');
    expect(entry).not.toBeNull();
    expect(entry!.label).toBe('あ');
    expect(typeof entry!.at).toBe('number');
  });

  it('delegates targeting to the underlying defs', () => {
    const r = new InteractiveRegistry(defs);
    const hit = r.target({ x: 0.5, y: 0.5, z: -1 }, { x: 0, y: 0, z: 1 }, 10);
    expect(hit?.id).toBe('a');
  });
});

// ---------------------------------------------------------------------------
// 3. World-level M4→M5 contract + hotspot geometry
// ---------------------------------------------------------------------------

describe('INTERACTABLES (M4 → M5 vocabulary contract)', () => {
  it('has exactly 12 interactables with unique ids', () => {
    expect(INTERACTABLES.length).toBe(12);
    const ids = new Set(INTERACTABLES.map((d) => d.id));
    expect(ids.size).toBe(12);
  });

  it('has non-empty label, reading, description, message and action on every def', () => {
    for (const def of INTERACTABLES) {
      expect(def.label.trim()).not.toBe('');
      expect(def.reading.trim()).not.toBe('');
      expect(def.description.trim()).not.toBe('');
      expect(def.message.trim()).not.toBe('');
      expect(def.action.trim()).not.toBe('');
    }
  });

  it('labels and readings are Japanese text (M5 lesson content)', () => {
    const japanese = /[\u3040-\u30ff\u3400-\u9fff]/; // hiragana/katakana/kanji
    for (const def of INTERACTABLES) {
      expect(def.label, def.id).toMatch(japanese);
      expect(def.reading, def.id).toMatch(japanese);
    }
  });

  it('covers 8 shops, 3 street props and the monument', () => {
    const shops = INTERACTABLES.filter((d) => d.id.startsWith('shop-'));
    const props = INTERACTABLES.filter((d) => d.id.startsWith('prop-'));
    expect(shops).toHaveLength(8);
    expect(props).toHaveLength(3);
    expect(INTERACTABLES.some((d) => d.id === 'monument')).toBe(true);
  });

  it('is accepted by the registry as a coherent data set', () => {
    const registry = new InteractiveRegistry(INTERACTABLES);
    expect(registry.size).toBe(12);
    for (const def of INTERACTABLES) {
      expect(registry.get(def.id)).toBe(def);
    }
  });
});

describe('hotspot geometry vs collision solids', () => {
  // Collision solids the player cannot enter: building footprints, lamp
  // poles (the M3 pole boxes) and the monument plinth (raw footprint; the
  // monument's own hotspot intentionally stands in front of it).
  const solids: Aabb3[] = [
    ...BUILDING_BASES.map((b) => ({
      minX: b.x - b.w / 2,
      maxX: b.x + b.w / 2,
      minY: 0,
      maxY: b.h,
      minZ: b.z - b.depth / 2,
      maxZ: b.z + b.depth / 2,
    })),
    ...STREET_LAMPS.map((l) => ({
      minX: l.x - LAMP_POLE_HALF.x,
      maxX: l.x + LAMP_POLE_HALF.x,
      minY: 0,
      maxY: 12,
      minZ: l.z - LAMP_POLE_HALF.z,
      maxZ: l.z + LAMP_POLE_HALF.z,
    })),
    {
      ...monumentFootprint(MONUMENT.scale),
      minY: 0,
      maxY: 12,
    },
  ];

  it('has every hotspot clear of the collision solids', () => {
    for (const def of INTERACTABLES) {
      for (const solid of solids) {
        expect(overlaps(def.box, solid), `${def.id} vs solid`).toBe(false);
      }
    }
  });

  it('keeps every hotspot inside the playable street bounds', () => {
    for (const def of INTERACTABLES) {
      expect(def.box.minX, def.id).toBeGreaterThanOrEqual(STREET.bounds.minX);
      expect(def.box.maxX, def.id).toBeLessThanOrEqual(STREET.bounds.maxX);
      expect(def.box.minZ, def.id).toBeGreaterThanOrEqual(STREET.bounds.minZ);
      expect(def.box.maxZ, def.id).toBeLessThanOrEqual(STREET.bounds.maxZ);
    }
  });

  it('anchors every shop slab to its building facade, road-side', () => {
    // Definition order is BUILDING_BASES order (one shop per building).
    const expectedIds = [
      'shop-ramen-ya', 'shop-hon-ya', 'shop-wagashi', 'shop-kissaten',
      'shop-konbini', 'shop-hana-ya', 'shop-zakka-ten', 'shop-sento',
    ];
    const shops = INTERACTABLES.slice(0, BUILDING_BASES.length);
    expect(shops.map((d) => d.id)).toEqual(expectedIds);

    for (let i = 0; i < BUILDING_BASES.length; i++) {
      const def = shops[i];
      const b = BUILDING_BASES[i];
      const face = b.x - (b.x > 0 ? 1 : -1) * (b.w / 2);
      // The slab's outer face is flush with the facade (touching, never
      // inside), and the slab extends 0.2 m toward the road.
      if (b.x > 0) {
        expect(def.box.maxX).toBeCloseTo(face, 9);
        expect(def.box.minX).toBeCloseTo(face - 0.2, 9);
      } else {
        expect(def.box.minX).toBeCloseTo(face, 9);
        expect(def.box.maxX).toBeCloseTo(face + 0.2, 9);
      }
      // Slab is road-side of the building: strictly outside its footprint.
      const inBuilding = def.box.minX < b.x + b.w / 2 && def.box.maxX > b.x - b.w / 2;
      expect(inBuilding).toBe(false);
    }
  });
});
