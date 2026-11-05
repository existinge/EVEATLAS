import { describe, expect, it } from 'vitest';
import {
  MONUMENT,
  STREET,
  STREET_PROPS,
  monumentFootprint,
  monumentPosition,
  streetPropTransform,
} from '../src/world/ShoppingStreet';

/** World-space AABB a prop really occupies once placed. 180° flips do not
 *  change an AABB, so this is independent of the flip choice. */
function propWorldFootprint(prop: (typeof STREET_PROPS)[number]) {
  const t = streetPropTransform(prop);
  const s = prop.scale;
  return {
    minX: t.position[0] + prop.boundsMin.x * s,
    maxX: t.position[0] + prop.boundsMax.x * s,
    minZ: t.position[2] + prop.boundsMin.z * s,
    maxZ: t.position[2] + prop.boundsMax.z * s,
  };
}

function overlaps(a: { minX: number; maxX: number; minZ: number; maxZ: number }, b: { minX: number; maxX: number; minZ: number; maxZ: number }): boolean {
  return a.minX < b.maxX && a.maxX > b.minX && a.minZ < b.maxZ && a.maxZ > b.minZ;
}

describe('M2 monument grounding (Y-down fix)', () => {
  it('grounds its BASE (max-Y end) on y ≈ 0 instead of raising the top', () => {
    const p = monumentPosition();
    // Old formula raised the splat by -boundsMin.y*scale (~3.0 m); the correct
    // settle puts the base slab at world y=0 via +boundsMax.y*scale.
    expect(p.y).toBeCloseTo(MONUMENT.boundsMax.y * MONUMENT.scale, 9);
    expect(p.y).toBeCloseTo(0.0043 * 7, 9);
    expect(Math.abs(p.y)).toBeLessThan(0.05);
    // x/z still re-center the model on its footprint.
    expect(p.x).toBeCloseTo(-MONUMENT.center.x * MONUMENT.scale, 9);
    expect(p.z).toBeCloseTo(-MONUMENT.center.z * MONUMENT.scale, 9);
  });
});

describe('M3 street props', () => {
  it('declares exactly the three M3 captures', () => {
    const names = STREET_PROPS.map((p) => p.name).sort();
    expect(names).toEqual(['apple', 'brass-diya-lantern', 'concrete-cat-statue']);
    // wine-barrel.ksplat exists in assets but is NOT a milestone M3 prop.
    expect(names).not.toContain('wine-barrel');
  });

  it('grounds every prop base at world y ≈ 0 (same ground line as M2)', () => {
    for (const prop of STREET_PROPS) {
      const t = streetPropTransform(prop);
      // transform grounds the file max-Y (BASE) end: worldBase = +boundsMax.y*scale
      expect(t.position[1]).toBeCloseTo(prop.boundsMax.y * prop.scale, 9);
      // After the vertical flip the model's lowest point is exactly at y=0.
      const worldMinY = t.position[1] - prop.boundsMax.y * prop.scale;
      expect(worldMinY).toBeCloseTo(0, 9);
    }
  });

  it('uses a unit 180° vertical flip (not the broken Euler hack)', () => {
    for (const prop of STREET_PROPS) {
      const [x, y, z, w] = prop.flip;
      const lenSq = x * x + y * y + z * z + w * w;
      expect(lenSq).toBeCloseTo(1, 9);
      // Exactly one of the two allowed flips: Z-flip [0,0,1,0] or X-flip [1,0,0,0].
      const isZFlip = x === 0 && y === 0 && z === 1 && w === 0;
      const isXFlip = x === 1 && y === 0 && z === 0 && w === 0;
      expect(isZFlip || isXFlip).toBe(true);
    }
  });

  it('points every prop face toward the street (+z)', () => {
    for (const prop of STREET_PROPS) {
      const zAxis = prop.flip[2]; // 1 for Z-flip, 0 for X-flip
      // The cat's face lives on local -z (head side); the others face local +z.
      const localFace = prop.name === 'concrete-cat-statue' ? -1 : +1;
      // Z-flip keeps local z facing; X-flip reverses it (local -z → world +z).
      const worldZ = localFace * (zAxis === 1 ? 1 : -1);
      expect(worldZ, prop.name).toBe(1);
    }
  });

  it('places each prop on the road, clear of the monument and spawn corridor', () => {
    const spawn = { run: [0, 8] as const, corridorX: 0.76 }; // PlayerController spawn + radius
    const m = monumentFootprint(MONUMENT.scale);

    for (const prop of STREET_PROPS) {
      const f = propWorldFootprint(prop);
      // On the road strip (|x| < roadHalf, within street bounds).
      expect(f.maxX).toBeLessThanOrEqual(STREET.roadHalf + 0.001);
      expect(f.minX).toBeGreaterThanOrEqual(-STREET.roadHalf - 0.001);
      expect(f.minZ).toBeGreaterThanOrEqual(STREET.bounds.minZ + 0.001);
      expect(f.maxZ).toBeLessThanOrEqual(STREET.bounds.maxZ - 0.001);

      // Clear of the monument's collision footprint.
      expect(overlaps(f, m), `${prop.name} hits monument collider`).toBe(false);
      // Clear of the player spawn corridor (x ≈ 0 in front of spawn z = 8).
      expect(Math.min(Math.abs(f.minX), Math.abs(f.maxX)), `${prop.name} inside spawn corridor`).toBeGreaterThanOrEqual(spawn.corridorX);
    }
  });

  it('keeps distinct street slots: no two props share a footprint', () => {
    const fs = STREET_PROPS.map((p) => propWorldFootprint(p));
    for (let i = 0; i < fs.length; i++) {
      for (let j = i + 1; j < fs.length; j++) {
        expect(overlaps(fs[i], fs[j]), `prop ${i} overlaps prop ${j}`).toBe(false);
      }
    }
  });
});