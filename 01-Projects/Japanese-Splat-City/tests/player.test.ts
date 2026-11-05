import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { PlayerController, type PlayerInput } from '../src/engine/PlayerController';
import { buildStreetWorld, pointInRect, distToRect } from '../src/world/Colliders';
import { BUILDING_BASES, MONUMENT, STREET, monumentFootprint } from '../src/world/ShoppingStreet';

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

describe('street collision world', () => {
  it('builds one collider per building plus the street monument', () => {
    const world = buildStreetWorld();
    expect(world.buildings).toHaveLength(BUILDING_BASES.length + 1);
    for (let i = 0; i < BUILDING_BASES.length; i++) {
      const b = BUILDING_BASES[i];
      const r = world.buildings[i];
      expect(r.minX).toBeCloseTo(b.x - b.w / 2, 6);
      expect(r.maxX).toBeCloseTo(b.x + b.w / 2, 6);
      expect(r.minZ).toBeCloseTo(b.z - b.depth / 2, 6);
      expect(r.maxZ).toBeCloseTo(b.z + b.depth / 2, 6);
    }
    // The appended monument collider (index BUILDING_BASES.length) is the
    // raw splat footprint; PlayerController pads it by the radius at query
    // time, keeping visual and collision in sync through MONUMENT /
    // monumentFootprint.
    const m = world.buildings[BUILDING_BASES.length];
    const f = monumentFootprint(MONUMENT.scale);
    expect(m.minX).toBeCloseTo(f.minX, 9);
    expect(m.maxX).toBeCloseTo(f.maxX, 9);
    expect(m.minZ).toBeCloseTo(f.minZ, 9);
    expect(m.maxZ).toBeCloseTo(f.maxZ, 9);
  });

  it('clamps the player inside the street bounds', () => {
    const world = buildStreetWorld();
    expect(world.bounds.minX).toBe(STREET.bounds.minX);
    expect(world.bounds.maxZ).toBe(STREET.bounds.maxZ);
  });

  it('pointInRect and distToRect behave on a unit rectangle', () => {
    const r = { minX: 1, maxX: 3, minZ: 1, maxZ: 3 };
    expect(pointInRect(2, 2, r)).toBe(true);
    expect(pointInRect(1, 2, r)).toBe(false);
    expect(distToRect(2, 2, r)).toBe(0);
    expect(distToRect(5, 2, r)).toBeCloseTo(2, 6);
    expect(distToRect(5, 5, r)).toBeCloseTo(Math.SQRT2 * 2, 6);
  });
});

describe('PlayerController movement', () => {
  it('walking forward for one second moves ~3 m toward -Z and stays grounded', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    walk(p, 1, { ...noInput(), forward: true });
    expect(p.position.z).toBeLessThan(8 - 3.3);
    expect(p.position.z).toBeGreaterThan(8 - 3.6);
    expect(p.position.x).toBeCloseTo(0, 4);
    expect(p.position.y).toBe(0);
    expect(p.onGround).toBe(true);
  });

  it('strafe keys move perpendicular to the view direction', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    // Facing -Z; right is +X.
    walk(p, 0.5, { ...noInput(), right: true });
    expect(p.position.x).toBeGreaterThan(1);
    expect(p.position.z).toBeCloseTo(8, 2);
  });

  it('sprinting covers noticeably more ground than walking', () => {
    const a = new PlayerController(undefined, buildStreetWorld());
    const b = new PlayerController(undefined, buildStreetWorld());
    walk(a, 1, { ...noInput(), forward: true });
    walk(b, 1, { ...noInput(), forward: true, sprint: true });
    expect(b.position.z).toBeLessThan(a.position.z - 1.5);
  });

  it('camera sits at eye height above the feet and matches the pose', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    p.applyMouseLook(100, 20);
    p.update(1 / 60, { ...noInput(), forward: true }, camera);
    expect(camera.position.y).toBeCloseTo(p.position.y + 1.7, 5);
    expect(camera.rotation.x).toBe(p.pitch);
    expect(camera.rotation.y).toBe(p.yaw);
  });
});

describe('PlayerController collision', () => {
  // West row building: center x=9, width 10 -> footprint x in [4, 14] with
  // z span [-37, -29]. Player radius 0.38 -> stops at x = 3.62.
  const world = buildStreetWorld();
  const FACE_X = 4 - 0.38;

  it('stops at the building face instead of passing through', () => {
    const p = new PlayerController(undefined, world);
    p.position.set(0, 0, -32); // right in front of the face
    p.applyMouseLook(Math.PI / 2 / 0.0022, 0); // yaw = -PI/2, facing +X
    walk(p, 3, { ...noInput(), forward: true });
    expect(p.position.x).toBeGreaterThanOrEqual(FACE_X - 1e-6);
    expect(p.position.x).toBeLessThanOrEqual(FACE_X + 0.01);
    expect(p.position.x).toBeLessThan(4); // never inside the footprint
  });

  it('slides along the face when walking diagonally into it', () => {
    const p = new PlayerController(undefined, world);
    p.position.set(3.5, 0, -32);
    p.applyMouseLook(Math.PI / 4 / 0.0022, 0); // 45° left of forward -> (0.71, -0.71)
    walk(p, 1, { ...noInput(), forward: true });
    expect(p.position.x).toBeLessThanOrEqual(FACE_X + 0.01);
    // The -Z component of the diagonal motion is preserved (sliding).
    expect(p.position.z).toBeLessThan(-32 - 0.7);
  });

  it('never enters a building or monument footprint, even when rounding a corner', () => {
    const p = new PlayerController(undefined, world);
    p.applyMouseLook(Math.PI / 4 / 0.0022, 0);
    let t = 0;
    while (t < 5) {
      p.update(1 / 60, { ...noInput(), forward: true }, camera);
      for (const b of world.buildings) {
        expect(pointInRect(p.position.x, p.position.z, b)).toBe(false);
      }
      t += 1 / 60;
    }
  });

  it('clamps to the playable bounds at the far edge', () => {
    const p = new PlayerController(undefined, world);
    // Lane x = 2.2: clear of the road-center monument (its padded span is
    // x ≈ ±1.45) and of both building rows (x ≤ -4 / x ≥ 4).
    p.position.set(2.2, 0, 8);
    walk(p, 30, { ...noInput(), forward: true });
    expect(p.position.z).toBeGreaterThanOrEqual(STREET.bounds.minZ + 0.38 - 1e-6);
    expect(p.position.z).toBeLessThanOrEqual(STREET.bounds.minZ + 0.38 + 1e-3);
  });

  it('blocks forward travel on the road at the monument', () => {
    const p = new PlayerController(undefined, world);
    // Spawns at (0, 0, 8) looking down -Z, straight into the monument that
    // stands at the road center (x = 0). The controller pads the raw
    // footprint by the player radius, so the stop face is m.maxZ + radius.
    walk(p, 6, { ...noInput(), forward: true });
    const m = world.buildings[BUILDING_BASES.length];
    const stop = m.maxZ + MONUMENT.playerRadius;
    expect(p.position.z).toBeGreaterThanOrEqual(stop - 1e-6);
    expect(p.position.z).toBeLessThanOrEqual(stop + 0.01);
    expect(p.position.z).toBeGreaterThan(-2); // never reached the bounds
    // A straight-on approach must NOT snap the player sideways around the
    // monument: the blocking axis owns the stop.
    expect(p.position.x).toBeCloseTo(0, 6);
  });

  it('lets the player pass the monument in the clear lane beside it', () => {
    const p = new PlayerController(undefined, world);
    p.position.set(2.2, 0, 8); // clear lane east of the monument
    walk(p, 6, { ...noInput(), forward: true });
    expect(p.position.z).toBeLessThan(-3); // well past the monument zone
    expect(p.position.x).toBe(2.2);
  });

  it('high-dt frames do not tunnel through a building', () => {
    const p = new PlayerController(undefined, world);
    p.position.set(0, 0, -32);
    p.applyMouseLook(Math.PI / 2 / 0.0022, 0); // face +X toward the west row
    walk(p, 3, { ...noInput(), forward: true, sprint: true }, 0.1);
    expect(p.position.x).toBeLessThanOrEqual(FACE_X + 0.01);
  });
});

describe('PlayerController physics', () => {
  it('jump leaves the ground and lands again without sinking', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    const input = { ...noInput(), jump: true };
    p.update(1 / 60, input, camera);
    input.jump = false;
    expect(p.onGround).toBe(false);
    expect(p.position.y).toBeGreaterThan(0);
    let peak = 0;
    let t = 0;
    while (t < 2) {
      p.update(1 / 60, input, camera);
      peak = Math.max(peak, p.position.y);
      if (p.onGround) break;
      t += 1 / 60;
    }
    // Peak height = v²/2g = 49/44 ≈ 1.11.
    expect(peak).toBeGreaterThan(0.9);
    expect(peak).toBeLessThan(1.25);
    expect(p.onGround).toBe(true);
    expect(p.position.y).toBe(0);
    expect(p.velocity.y).toBe(0);
  });

  it('grounded players do not accumulate downward velocity', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    walk(p, 0.5, noInput());
    expect(p.position.y).toBe(0);
    expect(p.velocity.y).toBe(0);
    expect(p.onGround).toBe(true);
  });
});

describe('PlayerController mouse look', () => {
  it('pitch clamps near vertical in both directions', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    p.applyMouseLook(0, 100000);
    expect(p.pitch).toBeCloseTo(-(Math.PI / 2 - 0.02), 6);
    p.applyMouseLook(0, -200000);
    expect(p.pitch).toBeCloseTo(Math.PI / 2 - 0.02, 6);
  });

  it('yaw wraps and horizontal look does not change pitch', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    const y0 = p.yaw;
    p.applyMouseLook(400, 12);
    expect(p.yaw).toBeCloseTo(y0 - 400 * 0.0022, 6);
    expect(p.pitch).toBeCloseTo(-12 * 0.0022, 6);
  });
});

describe('PlayerController reset', () => {
  it('returns to spawn with zero velocity', () => {
    const p = new PlayerController(undefined, buildStreetWorld());
    walk(p, 2, { ...noInput(), forward: true, sprint: true });
    p.applyMouseLook(300, 80);
    p.reset();
    expect(p.position.x).toBeCloseTo(0, 9);
    expect(p.position.y).toBeCloseTo(0, 9);
    expect(p.position.z).toBeCloseTo(8, 9);
    expect(p.velocity.lengthSq()).toBe(0);
    expect(p.yaw).toBe(0);
    expect(p.pitch).toBe(0);
    expect(p.onGround).toBe(true);
  });
});
