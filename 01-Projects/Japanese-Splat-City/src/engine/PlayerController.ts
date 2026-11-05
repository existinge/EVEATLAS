import * as THREE from 'three';
import type { Aabb2, StreetWorld } from '../world/Colliders';

/** Per-frame movement intent, produced by the DOM input layer. */
export interface PlayerInput {
  forward: boolean;
  back: boolean;
  left: boolean;
  right: boolean;
  sprint: boolean;
  /** True on the frame the jump key is pressed (edge-triggered). */
  jump: boolean;
}

export interface PlayerConfig {
  /** Spawn position of the player's feet. */
  spawn: { x: number; y: number; z: number };
  /** Initial look direction (radians). yaw=0 faces -Z, +yaw turns left. */
  spawnYaw?: number;
  spawnPitch?: number;
  /** Camera height above the feet. */
  eyeHeight: number;
  /** Horizontal collision radius (the player is a vertical capsule). */
  radius: number;
  walkSpeed: number;
  /** Sprint speed = walkSpeed * sprintMultiplier. */
  sprintMultiplier: number;
  /** How fast horizontal velocity converges to the target (1/s). */
  acceleration: number;
  /** How fast horizontal velocity decays with no input (1/s). */
  friction: number;
  gravity: number;
  jumpSpeed: number;
  /** Radians of mouse movement per pixel. */
  mouseSensitivity: number;
  /** Pitch clamp, radians from level. */
  maxPitch: number;
  groundY: number;
}

const DEFAULT_CONFIG: PlayerConfig = {
  spawn: { x: 0, y: 0, z: 8 },
  spawnYaw: 0,
  spawnPitch: 0,
  eyeHeight: 1.7,
  radius: 0.38,
  walkSpeed: 3.6,
  sprintMultiplier: 1.75,
  acceleration: 14,
  friction: 10,
  gravity: 22,
  jumpSpeed: 7,
  mouseSensitivity: 0.0022,
  maxPitch: Math.PI / 2 - 0.02,
  groundY: 0,
};

/**
 * First-person player controller.
 *
 * Pure simulation: no DOM, no renderer dependencies — only THREE math. This
 * keeps the controller unit-testable in Node (see tests/player.test.ts) and
 * lets M1 satisfy the "walk the street, turn the camera, stay on the street"
 * gate with evidence.
 */
export class PlayerController {
  /** Player feet position in world space. */
  readonly position = new THREE.Vector3();
  readonly velocity = new THREE.Vector3();
  yaw = 0;
  pitch = 0;
  /** True when the feet rest on groundY. */
  onGround = true;

  constructor(
    private readonly config: PlayerConfig = DEFAULT_CONFIG,
    private readonly world: StreetWorld = { buildings: [], bounds: { minX: -100, maxX: 100, minZ: -100, maxZ: 100 } },
  ) {
    this.reset();
  }

  applyMouseLook(dxPixels: number, dyPixels: number): void {
    this.yaw -= dxPixels * this.config.mouseSensitivity;
    this.pitch -= dyPixels * this.config.mouseSensitivity;
    const limit = this.config.maxPitch;
    this.pitch = Math.max(-limit, Math.min(limit, this.pitch));
  }

  reset(): void {
    const c = this.config;
    this.position.set(c.spawn.x, c.spawn.y, c.spawn.z);
    this.velocity.set(0, 0, 0);
    this.yaw = c.spawnYaw ?? 0;
    this.pitch = c.spawnPitch ?? 0;
    this.onGround = true;
  }

  /** Moves the simulation forward by dt and returns the camera transform. */
  update(dt: number, input: PlayerInput, camera: THREE.PerspectiveCamera): void {
    // --- Horizontal acceleration toward the target velocity.
    const speed = this.config.walkSpeed * (input.sprint ? this.config.sprintMultiplier : 1);
    const sin = Math.sin(this.yaw);
    const cos = Math.cos(this.yaw);
    // Local -Z (forward) and +X (right) directions in world space.
    const fwdX = -sin;
    const fwdZ = -cos;
    const rightX = cos;
    const rightZ = -sin;

    let dirX = 0;
    let dirZ = 0;
    if (input.forward) {
      dirX += fwdX;
      dirZ += fwdZ;
    }
    if (input.back) {
      dirX -= fwdX;
      dirZ -= fwdZ;
    }
    if (input.right) {
      dirX += rightX;
      dirZ += rightZ;
    }
    if (input.left) {
      dirX -= rightX;
      dirZ -= rightZ;
    }
    const len = Math.hypot(dirX, dirZ);
    if (len > 1e-4) {
      dirX /= len;
      dirZ /= len;
    }

    const blend = 1 - Math.exp(-this.config.acceleration * dt);
    const decay = 1 - Math.exp(-this.config.friction * dt);
    if (len > 1e-4) {
      this.velocity.x += (dirX * speed - this.velocity.x) * blend;
      this.velocity.z += (dirZ * speed - this.velocity.z) * blend;
    } else {
      this.velocity.x *= 1 - decay;
      this.velocity.z *= 1 - decay;
    }

    // --- Vertical: jump impulse, then gravity, then ground clamp.
    if (input.jump && this.onGround) {
      this.velocity.y = this.config.jumpSpeed;
      this.onGround = false;
    }
    this.velocity.y -= this.config.gravity * dt;
    let newY = this.position.y + this.velocity.y * dt;
    if (newY <= this.config.groundY) {
      newY = this.config.groundY;
      this.velocity.y = 0;
      this.onGround = true;
    }

    // --- Integrate XZ with collision resolution and bounds clamping.
    const { buildings, bounds } = this.world;
    let newX = this.position.x + this.velocity.x * dt;
    let newZ = this.position.z + this.velocity.z * dt;
    newX = this.resolveAxisX(newX, newZ, this.config.radius, buildings, bounds);
    newZ = this.resolveAxisZ(newX, newZ, this.config.radius, buildings, bounds);

    this.position.set(newX, newY, newZ);
    this.syncCamera(camera);
  }

  private resolveAxisX(
    candX: number,
    freeZ: number,
    radius: number,
    buildings: Aabb2[],
    bounds: Aabb2,
  ): number {
    let x = candX;
    // The player's position BEFORE this frame's move: used to decide which
    // axis was actually crossed this frame when the candidate enters a box.
    const prevZ = this.position.z;
    // Building push-out on the X axis.
    for (const b of buildings) {
      if (x <= b.minX - radius || x >= b.maxX + radius) continue;
      if (freeZ <= b.minZ - radius || freeZ >= b.maxZ + radius) continue;
      // This collider's Z band was only entered by this frame's move, so the
      // Z axis is the one being hit (straight-on approach, e.g. the street
      // monument); let resolveAxisZ stop the player instead of snapping
      // sideways around the box.
      if (prevZ <= b.minZ - radius || prevZ >= b.maxZ + radius) continue;
      // Inside the expanded rect: push to the nearest vertical face.
      const toMin = x - (b.minX - radius);
      const toMax = b.maxX + radius - x;
      x = toMin < toMax ? b.minX - radius : b.maxX + radius;
    }
    // Bounds clamp.
    return Math.max(bounds.minX + radius, Math.min(bounds.maxX - radius, x));
  }

  private resolveAxisZ(
    resolvedX: number,
    candZ: number,
    radius: number,
    buildings: Aabb2[],
    bounds: Aabb2,
  ): number {
    let z = candZ;
    // See resolveAxisX: only slide along X walls when the X span was already
    // overlapped before this frame's move.
    const prevX = this.position.x;
    for (const b of buildings) {
      if (z <= b.minZ - radius || z >= b.maxZ + radius) continue;
      if (resolvedX <= b.minX - radius || resolvedX >= b.maxX + radius) continue;
      if (prevX <= b.minX - radius || prevX >= b.maxX + radius) continue;
      const toMin = z - (b.minZ - radius);
      const toMax = b.maxZ + radius - z;
      z = toMin < toMax ? b.minZ - radius : b.maxZ + radius;
    }
    return Math.max(bounds.minZ + radius, Math.min(bounds.maxZ - radius, z));
  }

  /**
   * Applies the current pose to the given camera. The returned camera is used
   * by the renderer; this is the only place the camera is written to.
   */
  syncCamera(camera: THREE.PerspectiveCamera): void {
    camera.position.set(
      this.position.x,
      this.position.y + this.config.eyeHeight,
      this.position.z,
    );
    camera.rotation.order = 'YXZ';
    camera.rotation.set(this.pitch, this.yaw, 0);
  }
}