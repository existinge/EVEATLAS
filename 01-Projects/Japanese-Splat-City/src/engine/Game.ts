import * as THREE from 'three';
import {
  LogLevel,
  RenderMode,
  SceneRevealMode,
  Viewer,
} from '@mkkellogg/gaussian-splats-3d';
import { SceneManager } from './SceneManager';
import { MONUMENT, ShoppingStreet, monumentPosition } from '../world/ShoppingStreet';
import { buildStreetWorld } from '../world/Colliders';
import { PlayerController } from './PlayerController';
import { InputController } from './InputController';
import { MenuOverlay, type QualityPreset } from '../ui/MenuOverlay';

/**
 * Central game composition root.
 *
 * Owns the renderer, the scene, the camera and the main loop, and drives the
 * first-person player (M1). Later milestones attach interaction, missions and
 * learning systems to {@link update} the same way.
 */
export class Game {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene: THREE.Scene;
  readonly camera: THREE.PerspectiveCamera;
  readonly sceneManager: SceneManager;
  readonly player: PlayerController;
  readonly input: InputController;

  private readonly overlay: MenuOverlay;
  private readonly colliders = buildStreetWorld();

  /**
   * Gaussian-splat viewer (M2). Bound to our renderer/camera/threeScene; we
   * drive it manually via {@link Viewer.update} + {@link Viewer.render} each
   * frame because selfDrivenMode is off. Loading is non-blocking: the game
   * starts and runs normally while the monument splat streams in.
   */
  private readonly viewer: Viewer;

  private readonly clock = new THREE.Clock();
  private rafId = 0;
  private running = false;
  private disposed = false;
  /** True while pointer lock is held and the player may move. */
  private playing = false;

  constructor(container: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setClearColor(new THREE.Color(0x9ec8e8), 1);
    container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      75,
      container.clientWidth / Math.max(1, container.clientHeight),
      0.05,
      500,
    );

    this.sceneManager = new SceneManager(this.scene, this.camera);

    // Milestone M3 replaces this placeholder street with the detailed
    // Japanese shopping street; the module keeps growing in place. Collision
    // uses the same footprint data via buildStreetWorld().
    this.sceneManager.add(new ShoppingStreet().group);

    // ----- M2: gaussian-splat street monument ---------------------------
    // Viewer renders our scene + the splat mesh into the same renderer. The
    // renderer/camera/scene are external, so the viewer takes over neither
    // clear color, size, camera movement, nor input handlers.
    this.viewer = new Viewer({
      renderer: this.renderer,
      camera: this.camera,
      threeScene: this.scene,
      renderMode: RenderMode.Always, // re-render every frame, like the game loop
      selfDrivenMode: false, // host drives update()/render()
      useBuiltInControls: false, // player controls own the camera
      sharedMemoryForWorkers: false, // M2 requirement (no SharedArrayBuffer)
      showLoadingUI: false,
      logLevel: LogLevel.None,
      sceneRevealMode: SceneRevealMode.Instant,
    });

    // Kick off the load without awaiting: the game stays playable while the
    // splat streams in. Position comes from monumentPosition() so the visual
    // rests on the ground exactly where the AABB collider (index 8) sits.
    const monumentPos = monumentPosition();
    void this.viewer.addSplatScene('/assets/splats/carved-bull-head.ksplat', {
      position: [monumentPos.x, monumentPos.y, monumentPos.z],
      scale: [MONUMENT.scale, MONUMENT.scale, MONUMENT.scale],
      showLoadingUI: false,
    });

    this.player = new PlayerController(undefined, this.colliders);
    this.player.syncCamera(this.camera);

    this.input = new InputController(this.renderer.domElement);

    this.overlay = new MenuOverlay(container, {
      onPlay: () => this.startPlaying(),
      onReset: () => this.resetPlayer(),
      onQuality: (q) => this.applyQuality(q),
    });
    this.overlay.show(false);

    document.addEventListener('pointerlockchange', this.onPointerLockChange);
    window.addEventListener('resize', this.handleResize);
    window.addEventListener('keydown', this.onKeyDown);
  }

  private readonly onPointerLockChange = (): void => {
    if (this.input.isLocked()) {
      this.playing = true;
      this.overlay.hide();
    } else {
      this.playing = false;
      this.overlay.show(true);
    }
  };

  private readonly onKeyDown = (e: KeyboardEvent): void => {
    if (e.code === 'KeyR') {
      // Reset works both in-game and from the paused menu.
      this.resetPlayer();
    }
  };

  private startPlaying(): void {
    this.input.requestLock();
    // If the browser enforces its post-Esc pointer-lock cooldown, the lock
    // silently fails and the overlay stays until the user clicks again.
  }

  /** Teleports the player back to the spawn point. */
  resetPlayer(): void {
    this.player.reset();
    this.player.syncCamera(this.camera);
  }

  private applyQuality(q: QualityPreset): void {
    const ratio =
      q === 'low' ? 1 : q === 'medium' ? 1.5 : Math.min(window.devicePixelRatio, 2);
    this.renderer.setPixelRatio(ratio);
    this.renderer.shadowMap.enabled = q !== 'low';
    if (this.renderer.shadowMap.enabled) {
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }
    this.renderer.setSize(this.renderer.domElement.clientWidth, this.renderer.domElement.clientHeight);
  }

  /** Renders one frame immediately (used for loading screens). */
  renderOnce(): void {
    this.renderer.render(this.scene, this.camera);
  }

  start(): void {
    if (this.running || this.disposed) return;
    this.running = true;
    this.clock.start();
    this.loop();
  }

  stop(): void {
    this.running = false;
    cancelAnimationFrame(this.rafId);
  }

  dispose(): void {
    this.stop();
    this.disposed = true;
    document.removeEventListener('pointerlockchange', this.onPointerLockChange);
    window.removeEventListener('resize', this.handleResize);
    window.removeEventListener('keydown', this.onKeyDown);
    this.input.dispose();
    this.overlay.hide();
    // Tear down the splat viewer (aborts the load, frees workers/buffers)
    // before disposing the renderer it renders into.
    void this.viewer.dispose();
    this.sceneManager.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }

  private loop = (): void => {
    if (!this.running) return;
    this.rafId = requestAnimationFrame(this.loop);
    const dt = Math.min(this.clock.getDelta(), 0.1);
    this.update(dt);
    // Street first (clears the buffer), then the splat pass on top with
    // autoClear disabled so the monument composites with correct depth.
    this.renderer.render(this.scene, this.camera);
    this.viewer.update(this.renderer, this.camera);
    this.viewer.render();
  };

  /**
   * Frame update hook. Feeds input into the player when pointer lock is held;
   * later milestones extend this with interaction, missions and learning
   * systems.
   */
  protected update(dt: number): void {
    if (!this.playing) return;

    const look = this.input.pullLookDelta();
    this.player.applyMouseLook(look.x, look.y);

    const keys = this.input.getPlayerInput();
    const movement = {
      forward: keys.forward,
      back: keys.back,
      left: keys.left,
      right: keys.right,
      sprint: keys.sprint,
      jump: this.input.consumeJump(),
    };
    this.player.update(dt, movement, this.camera);
  }

  private readonly handleResize = (): void => {
    const width = this.renderer.domElement.clientWidth || window.innerWidth;
    const height = this.renderer.domElement.clientHeight || window.innerHeight;
    this.camera.aspect = width / Math.max(1, height);
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  };
}