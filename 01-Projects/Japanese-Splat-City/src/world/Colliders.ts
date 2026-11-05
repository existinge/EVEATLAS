import { BUILDING_BASES, MONUMENT, STREET, monumentFootprint } from './ShoppingStreet';

/**
 * Axis-aligned rectangle collider in the XZ ground plane.
 *
 * Collision is kept fully separate from rendering: the street monument (M2)
 * is a Gaussian-splat model rendered by its own viewer, while gameplay only
 * queries these rectangles — so swapping visuals never touches collision.
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
 * drives the visible geometry, plus the street monument footprint (M2) —
 * both sourced from {@link ./ShoppingStreet}. The building colliders keep
 * their original order (indices 0..7, pairable with BUILDING_BASES); the
 * monument is appended last.
 */
export function buildStreetWorld(bounds: Aabb2 = STREET.bounds): StreetWorld {
  const buildings = BUILDING_BASES.map((b) => ({
    minX: b.x - b.w / 2,
    maxX: b.x + b.w / 2,
    minZ: b.z - b.depth / 2,
    maxZ: b.z + b.depth / 2,
  }));
  // Street monument: the visual is a Gaussian splat model; the collider here
  // is its raw footprint — PlayerController pads any collider by its radius
  // at query time (see MONUMENT.playerRadius), so no padding happens here.
  buildings.push(monumentFootprint(MONUMENT.scale));
  return { buildings, bounds };
}