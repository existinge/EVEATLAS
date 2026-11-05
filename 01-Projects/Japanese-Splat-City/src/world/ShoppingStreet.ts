import * as THREE from 'three';

/**
 * Japanese 商店街 (shopping street) environment.
 *
 * Created as a minimal, renderable street at milestone M0 (ground,
 * sidewalks, simple building boxes) and progressively detailed through
 * milestone M3 (storefronts, signage, convenience store, café, props).
 *
 * Layout (top-down): the road runs along Z (north-south) at x ≈ 0,
 * with sidewalks and buildings on the east (-x) and west (+x) sides.
 */
export const STREET = {
  roadWidth: 7,
  sidewalkWidth: 4,
  roadHalf: 3.5,
  sidewalkInner: 3.5,
  sidewalkOuter: 7.5,
  buildingDepth: 7,
  groundY: 0,
  /** Distance from the road center to the near face of the buildings. */
  buildingFront: 7.5,
  /** Playable bounds in the XZ plane. */
  bounds: { minX: -16, maxX: 16, minZ: -46, maxZ: 46 },
} as const;

/**
 * Building footprints (top-down, width along X, depth along Z). The same
 * constant drives both the visible geometry (below) and the collision
 * colliders in {@link ./Colliders} — a single source of truth so the visual
 * scene and the collision world can never drift apart.
 */
export const BUILDING_BASES: ReadonlyArray<{
  x: number;
  z: number;
  w: number;
  depth: number;
  h: number;
  color: number;
}> = [
  // West side (+x), z from -38 to 38.
  { x: STREET.buildingFront + 1.5, z: -33, w: 10, depth: 8, h: 11, color: 0xb8a98f },
  { x: STREET.buildingFront + 1.5, z: -16, w: 12, depth: 8, h: 13, color: 0xa8a1a0 },
  { x: STREET.buildingFront + 1.5, z: 4, w: 12, depth: 8, h: 9, color: 0xc2a498 },
  { x: STREET.buildingFront + 1.5, z: 22, w: 10, depth: 8, h: 12, color: 0x9fb0a0 },
  // East side (-x).
  { x: -(STREET.buildingFront + 1.5), z: -30, w: 10, depth: 8, h: 10, color: 0xa9b0bd },
  { x: -(STREET.buildingFront + 1.5), z: -10, w: 12, depth: 8, h: 14, color: 0xc0a892 },
  { x: -(STREET.buildingFront + 1.5), z: 12, w: 12, depth: 8, h: 11, color: 0x9dabb0 },
  { x: -(STREET.buildingFront + 1.5), z: 32, w: 10, depth: 8, h: 9, color: 0xb3a39b },
];

export class ShoppingStreet {
  readonly group = new THREE.Group();

  constructor() {
    this.buildGround();
    this.buildBuildings();
  }

  private buildGround(): void {
    const { roadWidth, sidewalkWidth, buildingDepth, groundY } = STREET;

    // Road (asphalt).
    const road = new THREE.Mesh(
      new THREE.PlaneGeometry(roadWidth, 96),
      new THREE.MeshStandardMaterial({ color: 0x3c3f46, roughness: 0.95 }),
    );
    road.rotation.x = -Math.PI / 2;
    road.position.set(0, groundY, 0);
    road.receiveShadow = true;
    this.group.add(road);

    // Sidewalks (one each side).
    for (const side of [-1, 1] as const) {
      const sidewalk = new THREE.Mesh(
        new THREE.PlaneGeometry(sidewalkWidth, 96),
        new THREE.MeshStandardMaterial({ color: 0x9a9a97, roughness: 0.9 }),
      );
      sidewalk.rotation.x = -Math.PI / 2;
      sidewalk.position.set(side * (STREET.roadHalf + sidewalkWidth / 2), groundY + 0.02, 0);
      sidewalk.receiveShadow = true;
      this.group.add(sidewalk);
    }

    // Back lots behind the buildings (keeps the playable area tidy).
    const back = new THREE.Mesh(
      new THREE.PlaneGeometry(20, 96),
      new THREE.MeshStandardMaterial({ color: 0x6f736d, roughness: 1 }),
    );
    back.rotation.x = -Math.PI / 2;
    back.position.set(0, groundY - 0.01, 0);
    back.receiveShadow = true;
    this.group.add(back);

    void buildingDepth;
  }

  private buildBuildings(): void {
    const { groundY } = STREET;
    for (const b of BUILDING_BASES) {
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(b.w, b.h, b.depth),
        new THREE.MeshStandardMaterial({ color: b.color, roughness: 0.85 }),
      );
      mesh.position.set(b.x, groundY + b.h / 2, b.z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      this.group.add(mesh);
    }
  }
}
