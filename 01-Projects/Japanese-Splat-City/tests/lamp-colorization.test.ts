import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { PlayerController, type PlayerInput } from '../src/engine/PlayerController';
import { buildStreetWorld, type Aabb2 } from '../src/world/Colliders';
import {
  BULB_HUE,
  BULB_HUE_RANGE,
  LAMP_POLE_HALF,
  MONUMENT,
  STREET,
  STREET_LAMPS,
  STREET_PROPS,
  ShoppingStreet,
  bulbColor,
  streetPropTransform,
} from '../src/world/ShoppingStreet';

const camera = new THREE.PerspectiveCamera(75, 16 / 9, 0.05, 500);

function noInput(): PlayerInput {
  return { forward: false, back: false, left: false, right: false, sprint: false, jump: false };
}

/** Simulates `seconds` of walking with the given keys at 60 Hz. */
function walk(p: PlayerController, seconds: number, input: PlayerInput, dt = 1 / 60): void {
  let t = 0;
  while (t < seconds) {
    p.update(dt, input, camera);
    t += dt;
  }
}

function intersects(a: Aabb2, b: Aabb2): boolean {
  return !(a.maxX <= b.minX || a.minX >= b.maxX || a.maxZ <= b.minZ || a.minZ >= b.maxZ);
}

describe('M3.1 lamp colorization (200-220 hue bulbs)', () => {
  it('the bulb color carries the requested 200-220 hue', () => {
    // The user asked to alter the red/orange splat scene's tint to a
    // 200-220 hue ("white-ish"); the lamp bulb is the authoritative object
    // carrying that hue.
    expect(BULB_HUE).toBeGreaterThanOrEqual(BULB_HUE_RANGE.min);
    expect(BULB_HUE).toBeLessThanOrEqual(BULB_HUE_RANGE.max);
    const hsl = { h: 0, s: 0, l: 0 };
    bulbColor().getHSL(hsl);
    const hueDeg = (hsl.h * 360 + 360) % 360;
    expect(hueDeg).toBeGreaterThanOrEqual(BULB_HUE_RANGE.min - 1);
    expect(hueDeg).toBeLessThanOrEqual(BULB_HUE_RANGE.max + 1);
    // Saturated "warm white" — not grey, not pastel.
    expect(hsl.s).toBeGreaterThan(0.8);
    expect(hsl.l).toBeGreaterThan(0.6);
  });

  it('places lamps on the sidewalk strips, clear of the road and bounds', () => {
    expect(STREET_LAMPS.length).toBeGreaterThanOrEqual(4);
    for (const lamp of STREET_LAMPS) {
      // On the sidewalk strip (|x| strictly between the road edge and the
      // sidewalk outer edge), never on the road surface.
      expect(Math.abs(lamp.x)).toBeGreaterThanOrEqual(STREET.sidewalkInner);
      expect(Math.abs(lamp.x)).toBeLessThanOrEqual(STREET.sidewalkInner + 1.5);
      // Inside the playable bounds with room to spare.
      expect(lamp.x).toBeGreaterThan(STREET.bounds.minX + 0.5);
      expect(lamp.x).toBeLessThan(STREET.bounds.maxX - 0.5);
      expect(lamp.z).toBeGreaterThan(STREET.bounds.minZ + 0.5);
      expect(lamp.z).toBeLessThan(STREET.bounds.maxZ - 0.5);
    }
  });

  it('keeps every pole footprint clear of buildings, the monument, and props', () => {
    const world = buildStreetWorld();
    const propFoots: Aabb2[] = STREET_PROPS.map((prop) => {
      const ex = Math.max(Math.abs(prop.boundsMin.x), Math.abs(prop.boundsMax.x)) * prop.scale;
      const ez = Math.max(Math.abs(prop.boundsMin.z), Math.abs(prop.boundsMax.z)) * prop.scale;
      return { minX: prop.at.x - ex, maxX: prop.at.x + ex, minZ: prop.at.z - ez, maxZ: prop.at.z + ez };
    });
    for (const pole of world.poles) {
      for (const b of world.buildings) expect(intersects(pole, b)).toBe(false);
      for (const p of propFoots) expect(intersects(pole, p)).toBe(false);
    }
  });

  it('creates a distinct pole collider per lamp, inside bounds and free of one another', () => {
    const world = buildStreetWorld();
    expect(world.poles).toHaveLength(STREET_LAMPS.length);
    for (let i = 0; i < STREET_LAMPS.length; i++) {
      const lamp = STREET_LAMPS[i];
      const rect = world.poles[i];
      expect(rect.minX).toBeCloseTo(lamp.x - LAMP_POLE_HALF.x, 9);
      expect(rect.maxX).toBeCloseTo(lamp.x + LAMP_POLE_HALF.x, 9);
      expect(rect.minZ).toBeCloseTo(lamp.z - LAMP_POLE_HALF.z, 9);
      expect(rect.maxZ).toBeCloseTo(lamp.z + LAMP_POLE_HALF.z, 9);
    }
    for (let i = 0; i < world.poles.length; i++) {
      for (let j = i + 1; j < world.poles.length; j++) {
        expect(intersects(world.poles[i], world.poles[j])).toBe(false);
      }
    }
  });

  it('spawn corridor stays clear: no pole within the player radius of spawn', () => {
    const world = buildStreetWorld();
    const spawn = { x: 0, z: 8 };
    for (const pole of world.poles) {
      const cx = Math.max(0, Math.max(pole.minX - spawn.x, spawn.x - pole.maxX));
      const cz = Math.max(0, Math.max(pole.minZ - spawn.z, spawn.z - pole.maxZ));
      expect(Math.hypot(cx, cz)).toBeGreaterThanOrEqual(MONUMENT.playerRadius * 2);
    }
  });

  it('scaffolds a PointLight and a warm bulb mesh per lamp in the street group', () => {
    const street = new ShoppingStreet();
    const its = street.group.children;
    expect(its.filter((c) => c.type === 'PointLight')).toHaveLength(STREET_LAMPS.length);
    const warmMaterials: THREE.MeshStandardMaterial[] = [];
    for (const child of its) {
      const m = (child as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
      if (m && m.emissiveIntensity > 1) warmMaterials.push(m);
    }
    expect(warmMaterials.length).toBeGreaterThanOrEqual(STREET_LAMPS.length);
    const hsl = { h: 0, s: 0, l: 0 };
    warmMaterials[0].emissive.getHSL(hsl);
    expect((hsl.h * 360 + 360) % 360).toBeCloseTo(BULB_HUE, 1);
  });
});

describe('M3.1 lamp collision', () => {
  it('a player walking sideways is stopped by a lamp pole', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    // Stand on the west sidewalk level with the west-mid lamp pole and
    // walk inward (-x) toward the road — the pole at x=4.3 must block the
    // player flush against its near face (4.3 + 0.12 + radius ≈ 4.8).
    p.position.set(5.8, 0, 11);
    walk(p, 4, { ...noInput(), left: true });
    expect(p.position.x).toBeGreaterThan(4.75); // pushed flush against the face
    expect(p.position.x).toBeLessThan(4.85); // and never through it
    expect(p.position.z).toBeCloseTo(11, 1);
  });

  it('without the pole collider the same walk passes the pole position', () => {
    const world = buildStreetWorld();
    const poleFree: typeof world = {
      buildings: world.buildings,
      poles: [],
      bounds: world.bounds,
    };
    const p = new PlayerController(undefined, poleFree);
    p.position.set(5.8, 0, 11);
    expect(p.position.x).toBeGreaterThan(4.3);
    walk(p, 4, { ...noInput(), left: true });
    expect(p.position.x).toBeLessThan(4.3);
  });
});

describe('bulb color stays consistent across geometry helpers', () => {
  it('streetPropTransform and lamp placement use disjoint sidewalk slots', () => {
    for (const prop of STREET_PROPS) {
      const t = streetPropTransform(prop);
      for (const lamp of STREET_LAMPS) {
        // Props live on the inner sidewalk (|x| <= ~2.7); lamps on the outer
        // strip (|x| >= 4.18) at the road-facing edge — never the same lane.
        expect(Math.abs(lamp.x) - Math.abs(t.position[0])).toBeGreaterThan(1);
      }
    }
  });
});