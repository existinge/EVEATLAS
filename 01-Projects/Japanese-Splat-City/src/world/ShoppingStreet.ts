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

/**
 * Street monument: a real Gaussian-splat model (carved bull head, CC0, see
 * public/assets/licenses/README.md) standing in the middle of the road at
 * x = 0, directly ahead of the player spawn. Milestone M2.
 *
 * Innerscene bakes splat models "Y-down": in object space the max-Y end is
 * the BASE (the plinth/slab under the feet) and the min-Y end points up at
 * the head/horns. So the splat is re-grounded with `y = +boundsMax.y * scale`
 * (NOT the old `-boundsMin.y * scale`, which grounded the inverted top end)
 * and the model is vertically flipped 180° — see monumentPosition's quaternion
 * in Game.ts — so the base sits on the ground and the head points up.
 * Object-space metrics below are measured from the actual splat data
 * (see facedir.mjs in .scratch-m3-parse/).
 *
 * This constant is the single source of truth for both the visual transform
 * ({@link monumentPosition}) and the collision footprint
 * ({@link monumentFootprint}, consumed by {@link ./Colliders}).
 */
export const MONUMENT = {
  /** Uniform scale applied to the splat model (meters per object unit). */
  scale: 7,
  /**
   * Player collision radius in meters; must match
   * PlayerController.DEFAULT_CONFIG.radius. The controller itself pads every
   * collider by this radius at query time (resolveAxisX/Z), so footprints in
   * this module stay raw — this field only documents that coupling.
   */
  playerRadius: 0.38,
  /** Object-space min corner of the splat, measured from splat data. */
  boundsMin: { x: -0.1475, y: -0.432, z: -0.1112 },
  /** Object-space max corner of the splat, measured from splat data. */
  boundsMax: { x: 0.1575, y: 0.0043, z: 0.1702 },
  /** Object-space center offset of the splat from the model origin. */
  center: { x: 0.005, y: -0.2138, z: 0.0295 },
} as const;

/**
 * World-space position that places the monument centered on the road (x = 0)
 * with its base slab resting on the ground (y = +boundsMax.y * scale). The x/z
 * terms re-center the model on its footprint: `-center * scale`.
 */
export function monumentPosition(scale: number = MONUMENT.scale): {
  x: number;
  y: number;
  z: number;
} {
  return {
    x: -MONUMENT.center.x * scale,
    y: MONUMENT.boundsMax.y * scale,
    z: -MONUMENT.center.z * scale,
  };
}

/**
 * World-space collision footprint of the monument — the raw splat rectangle,
 * NOT padded. PlayerController inflates every collider by its radius at query
 * time (see MONUMENT.playerRadius), exactly as it does for the building
 * footprints from BUILDING_BASES, so keeping this raw is required for
 * consistent block and slide behavior.
 *
 * Structurally a {@link ./Colliders.Aabb2}; declared inline to keep this
 * module free of imports from Colliders (which itself imports this module).
 */
export function monumentFootprint(scale: number = MONUMENT.scale): {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
} {
  return {
    minX: (MONUMENT.boundsMin.x - MONUMENT.center.x) * scale,
    maxX: (MONUMENT.boundsMax.x - MONUMENT.center.x) * scale,
    minZ: (MONUMENT.boundsMin.z - MONUMENT.center.z) * scale,
    maxZ: (MONUMENT.boundsMax.z - MONUMENT.center.z) * scale,
  };
}

/**
 * Milestone M3 street props: three fresh Innerscene captures placed at the
 * roadside (road half-width 3.5, off the monument and off the spawn corridor).
 * They were baked exactly like the monument — "Y-down": the file's max-Y end
 * is the BASE that must rest on the ground, the min-Y end is the TOP. So each
 * prop is re-grounded with `y = +boundsMax.y * scale` and vertically flipped
 * 180°.
 *
 * Facing (which way the prop looks toward the street): the Quaternion `flip`
 * is a *unit* 180° rotation, chosen so its +Z face ends up pointing +z (down
 * the road toward the player, since the player spawns at z=+8 facing -z).
 * - Z-flip `[0,0,1,0]` (180° about Z) negates x and y, keeps z. It rights the
 *   vertical AND preserves the +Z facing. Used when the model's face is on +z.
 * - X-flip `[1,0,0,0]` (180° about X) negates y and z, keeps x. It rights the
 *   vertical AND *reverses* the Z facing — used when the model's face is on
 *   -z (the cat statue's head), turning it +z. Safe because the cat's face
 *   plane is mirror-symmetric in x.
 *
 * Geometry is measured from the actual splat files (facedir.mjs,
 * .scratch-m3-parse/) which is why these constants live next to MONUMENT.
 */
export type StreetPropFlip = [number, number, number, number];

export interface StreetPropDef {
  /** Stable id used in docs/tests. */
  name: string;
  /** Path served by Vite (public/assets/splats/m3). */
  asset: string;
  /** Uniform object→meters scale, tuned so the prop looks life-sized. */
  scale: number;
  /** Object-space bounds, measured from splat data (Y-down bake). */
  boundsMin: { x: number; y: number; z: number };
  boundsMax: { x: number; y: number; z: number };
  center: { x: number; y: number; z: number };
  /** Street placement (world x, z). Chosen clear of the monument footprint
   *  and the player spawn corridor (see tests/street-props.test.ts). */
  at: { x: number; z: number };
  /** Unit 180° vertical flip (see module comment for Z- vs X-flip). */
  flip: StreetPropFlip;
  /** Diagnostic: which side the original model faces before the flip. */
  faceNote: string;
}

export const STREET_PROPS: readonly StreetPropDef[] = [
  {
    name: 'apple',
    asset: '/assets/splats/m3/apple.ksplat',
    scale: 0.6,
    boundsMin: { x: -0.286, y: -0.235, z: -0.28 },
    boundsMax: { x: 0.285, y: 0.25, z: 0.282 },
    center: { x: 0, y: 0.007, z: 0.001 },
    at: { x: 2.5, z: 3.5 },
    // Near-centrosymmetric, thin stem at min-Y (top). Z-flip keeps +Z facing.
    flip: [0, 0, 1, 0],
    faceNote: 'near-centrosymmetric; Z-flip preserves +Z',
  },
  {
    name: 'brass-diya-lantern',
    asset: '/assets/splats/m3/brass-diya-lantern.splat',
    scale: 1.2,
    boundsMin: { x: -0.055, y: -0.38, z: -0.054 },
    boundsMax: { x: 0.065, y: 0.004, z: 0.067 },
    center: { x: 0.005, y: -0.188, z: 0.006 },
    at: { x: -2.5, z: 1.5 },
    // Wide base disc at max-Y; thin finial spike at min-Y (top). Near
    // centrosymmetric in x/z, so Z-flip is safe and keeps +Z facing.
    flip: [0, 0, 1, 0],
    faceNote: 'near-centrosymmetric; Z-flip preserves +Z',
  },
  {
    name: 'concrete-cat-statue',
    asset: '/assets/splats/m3/concrete-cat-statue.splat',
    scale: 1.5,
    boundsMin: { x: -0.078, y: -0.282, z: -0.1 },
    boundsMax: { x: 0.074, y: 0.001, z: 0.149 },
    center: { x: -0.002, y: -0.141, z: 0.025 },
    at: { x: 2.6, z: -3.0 },
    // The head faces -z (its +z reach 0.15 wide tail side, -z reach 0.085
    // head side). X-flip rights the vertical AND swings the head to +z so the
    // cat looks down the street at the player. Face plane is mirror-symmetric
    // in x, so the X-flip cannot mirror the face wrongly.
    flip: [1, 0, 0, 0],
    faceNote: 'head faces -z; X-flip turns head to +Z',
  },
];

/**
 * World-space transform that puts a street prop on the ground and facing the
 * street: base grounded at world y ≈ 0 (`+boundsMax.y * scale`, the same
 * ground line as the M2 monument), re-centered on its street slot, vertically
 * flipped by the unit quaternion in {@link StreetPropDef.flip}.
 */
export function streetPropTransform(prop: StreetPropDef): {
  position: [number, number, number];
  rotation: StreetPropFlip;
  scale: [number, number, number];
} {
  return {
    position: [
      prop.at.x - prop.center.x * prop.scale,
      prop.boundsMax.y * prop.scale,
      prop.at.z - prop.center.z * prop.scale,
    ],
    rotation: prop.flip,
    scale: [prop.scale, prop.scale, prop.scale],
  };
}

/**
 * M3.1 colorization polish — street lamps (the deferred-M3 "lighting" item).
 *
 * Japanese shopping streets are lit at dusk by warm "azure/white" lamp bulbs
 * ringing the road. The color task asked for a bulb tint in the **200–220 hue
 * range**; this block is the authoritative in-code definition of that range
 * (theme, docs and tests all reference these constants). The bulb look is not
 * baked splat data — it is new procedural geometry plus a real PointLight per
 * lamp, so it can actually glow in the Three.js scene (unlike the fixed splat
 * colors).
 */
export const BULB_HUE_RANGE = { min: 200, max: 220 } as const;

/** The concrete hue (within {@link BULB_HUE_RANGE}) used for all lamp bulbs. */
export const BULB_HUE = 210;

/**
 * The lamp-bulb color: a saturated azure/cyan ("warm white") at BULB_HUE.
 * Shared by the emissive lamp geometry, the translucent glass shade and each
 * lamp's PointLight so the glow reads consistently everywhere.
 */
export function bulbColor(): THREE.Color {
  return new THREE.Color().setHSL(BULB_HUE / 360, 0.9, 0.72);
}

/** Half-extents (meters) of a lamp pole's collision footprint. */
export const LAMP_POLE_HALF = { x: 0.12, z: 0.35 } as const;

export interface StreetLampDef {
  /** Stable id used in docs/tests. */
  id: string;
  /** World x/z of the pole base. */
  x: number;
  z: number;
}

/**
 * Street lamps on the sidewalk strips, one per building gap so no lamp pierces
 * a building footprint; each is staggered along the road away from the spawn
 * corridor (|x| ≈ 0, z ≈ 8) and far from the monument and M3 prop footprints.
 * The arm + bulb reach inward toward the road so the glow lights the walkway.
 */
export const STREET_LAMPS: readonly StreetLampDef[] = [
  { id: 'west-north', x: 4.3, z: -5 },
  { id: 'west-mid', x: 4.3, z: 11 },
  { id: 'west-south', x: 4.3, z: 31 },
  { id: 'east-north', x: -4.3, z: -21 },
  { id: 'east-mid', x: -4.3, z: 1 },
  { id: 'east-south', x: -4.3, z: 22 },
] as const;

export class ShoppingStreet {
  readonly group = new THREE.Group();

  constructor() {
    this.buildGround();
    this.buildBuildings();
    this.buildLamps();
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

  /**
   * Street lamps (M3.1): dark pole + arm reaching toward the road, an emissive
   * bulb at BULB_HUE, a translucent glass shade, and a PointLight so the bulb
   * actually throws warm azure light onto the street at night.
   */
  private buildLamps(): void {
    const { groundY } = STREET;
    const bulb = bulbColor();
    for (const lamp of STREET_LAMPS) {
      // Arm direction: inward, toward the road (x = 0).
      const dir = lamp.x > 0 ? -1 : 1;
      const bulbX = lamp.x + dir * 0.85;

      const dark = new THREE.MeshStandardMaterial({
        color: 0x2a2d33,
        roughness: 0.55,
        metalness: 0.7,
      });

      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.08, 3.4, 10), dark);
      pole.position.set(lamp.x, groundY + 1.7, lamp.z);
      pole.castShadow = true;
      this.group.add(pole);

      const arm = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.06, 0.06), dark);
      arm.position.set(lamp.x + dir * 0.45, groundY + 3.32, lamp.z);
      arm.castShadow = true;
      this.group.add(arm);

      // Emissive bulb core.
      const bulbMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.09, 12, 10),
        new THREE.MeshStandardMaterial({
          color: bulb.clone(),
          emissive: bulb.clone(),
          emissiveIntensity: 2.4,
          roughness: 0.4,
        }),
      );
      bulbMesh.position.set(bulbX, groundY + 3.18, lamp.z);
      this.group.add(bulbMesh);

      // Translucent glass shade wrapping the bulb.
      const shade = new THREE.Mesh(
        new THREE.SphereGeometry(0.16, 12, 10),
        new THREE.MeshStandardMaterial({
          color: bulb.clone(),
          emissive: bulb.clone(),
          emissiveIntensity: 0.6,
          transparent: true,
          opacity: 0.4,
        }),
      );
      shade.position.set(bulbX, groundY + 3.18, lamp.z);
      this.group.add(shade);

      // Real light source tinted with the same bulb color.
      const light = new THREE.PointLight(bulb.clone(), 2.2, 10, 2);
      light.position.set(bulbX, groundY + 3.15, lamp.z);
      this.group.add(light);
    }
  }
}
