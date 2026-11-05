import { BUILDING_BASES, STREET } from './ShoppingStreet';

/**
 * Axis-aligned rectangle collider in the XZ ground plane.
 *
 * Collision is kept fully separate from rendering: visible meshes can be
 * replaced by Gaussian splat models (or any other visual) at milestone M2
 * without touching the collision world, because gameplay never queries the
 * scene graph — it queries these rectangles.
 */
export interface Aabb2 {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
}

/**
 * All colliders that make up the playable street, plus the outer bounds the
 * player is clamped to.
 */
export interface StreetWorld {
  buildings: Aabb2[];
  bounds: Aabb2;
}

/** True when a point is strictly inside a rectangle. */
export function pointInRect(x: number, z: number, r: Aabb2): boolean {
  return x > r.minX && x < r.maxX && z > r.minZ && z < r.maxZ;
}

/** Distance from point to the nearest point on the rectangle (0 when inside). */
export function distToRect(x: number, z: number, r: Aabb2): number {
  const cx = Math.max(r.minX, Math.min(x, r.maxX));
  const cz = Math.max(r.minZ, Math.min(z, r.maxZ));
  return Math.hypot(x - cx, z - cz);
}

/**
 * Builds the collision world from the same BUILDING_BASES constant that
 * drives the visible geometry (single source of truth).
 */
export function buildStreetWorld(bounds: Aabb2 = STREET.bounds): StreetWorld {
  const buildings = BUILDING_BASES.map((b) => ({
    minX: b.x - b.w / 2,
    maxX: b.x + b.w / 2,
    minZ: b.z - b.depth / 2,
    maxZ: b.z + b.depth / 2,
  }));
  return { buildings, bounds };
}