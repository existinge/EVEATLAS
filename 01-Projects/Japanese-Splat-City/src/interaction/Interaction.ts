/**
 * Milestone M4 — interaction core: pure data types and ray-vs-box math.
 *
 * This module is deliberately renderer- and DOM-free so it can be unit-tested
 * headlessly and reused by later milestones. {@link InteractiveDef} is ALSO the
 * data contract for M5 (vocabulary learning): the Japanese label, its reading
 * and the description are exactly the fields the vocabulary overlay will
 * consume, so M4 and M5 share a single hook instead of duplicating mechanisms.
 */

export interface Vec3Like {
  x: number;
  y: number;
  z: number;
}

/** Axis-aligned interaction box in world space (meters). */
export interface Aabb3 {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  minZ: number;
  maxZ: number;
}

/**
 * A targetable, interactable object in the street.
 *
 * `label` / `reading` / `description` double as the vocabulary data contract
 * for milestone M5 — do not extend this shape for M5 without updating the
 * vocabulary schema there too.
 */
export interface InteractiveDef {
  /** Stable id, e.g. `shop-ramen-ya`, `prop-apple`, `monument`. */
  id: string;
  /** Japanese display label — the vocabulary word (M5 contract). */
  label: string;
  /** Reading in hiragana/katakana (M5 contract). */
  reading: string;
  /** Short Japanese description shown under the label while targeting. */
  description: string;
  /** What the player "does" — shown after pressing E (M5 contract). */
  message: string;
  /** Short verb shown in the E-hint, e.g. 「買う」. */
  action: string;
  /** World-space box the target ray must intersect (see {@link Aabb3}). */
  box: Aabb3;
}

/**
 * Slab-method ray/AABB intersection. Returns the entry distance in meters
 * (the direction vector is normalized internally, so any non-zero `dir`
 * works), or null when the ray misses the box or exits beyond `maxDistance`.
 * An origin inside the box returns 0.
 */
export function rayAabb3(
  origin: Vec3Like,
  dir: Vec3Like,
  box: Aabb3,
  maxDistance: number = Infinity,
): number | null {
  const invLen = 1 / Math.hypot(dir.x, dir.y, dir.z);
  const dx = dir.x * invLen;
  const dy = dir.y * invLen;
  const dz = dir.z * invLen;

  let tMin = 0;
  let tMax = maxDistance;

  const axes: Array<keyof Vec3Like> = ['x', 'y', 'z'];
  const mins = { x: box.minX, y: box.minY, z: box.minZ };
  const maxs = { x: box.maxX, y: box.maxY, z: box.maxZ };
  for (const axis of axes) {
    const d = axis === 'x' ? dx : axis === 'y' ? dy : dz;
    const o = origin[axis];
    if (Math.abs(d) < 1e-9) {
      // Ray parallel to this slab: must already be inside it.
      if (o < mins[axis] || o > maxs[axis]) return null;
      continue;
    }
    let t1 = (mins[axis] - o) / d;
    let t2 = (maxs[axis] - o) / d;
    if (t1 > t2) {
      const swap = t1;
      t1 = t2;
      t2 = swap;
    }
    tMin = Math.max(tMin, t1);
    tMax = Math.min(tMax, t2);
    if (tMin > tMax) return null;
  }
  return tMin;
}

/**
 * Nearest target for a ray: the def whose box is hit first, or null when
 * nothing is hit within `maxDistance`. Boxes may overlap; the closest hit
 * wins deterministically.
 */
export function interactionTarget(
  defs: readonly InteractiveDef[],
  origin: Vec3Like,
  dir: Vec3Like,
  maxDistance: number,
): InteractiveDef | null {
  let best: InteractiveDef | null = null;
  let bestT = maxDistance;
  for (const def of defs) {
    const t = rayAabb3(origin, dir, def.box, bestT);
    if (t !== null) {
      best = def;
      bestT = t;
    }
  }
  return best;
}
