import { describe, expect, it } from 'vitest';
import { ShoppingStreet, STREET } from '../src/world/ShoppingStreet';
import * as THREE from 'three';

describe('ShoppingStreet scaffold', () => {
  it('builds a non-empty scene group', () => {
    const street = new ShoppingStreet();
    let meshCount = 0;
    street.group.traverse((obj) => {
      if (obj instanceof THREE.Mesh) meshCount += 1;
    });
    expect(meshCount).toBeGreaterThan(0);
  });

  it('exposes sane street constants', () => {
    expect(STREET.roadWidth).toBeGreaterThan(0);
    expect(STREET.bounds.minX).toBeLessThan(STREET.bounds.maxX);
    expect(STREET.bounds.minZ).toBeLessThan(STREET.bounds.maxZ);
  });
});
