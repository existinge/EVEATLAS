import * as THREE from 'three';
import { SceneManager } from './SceneManager';
import { ShoppingStreet } from '../world/ShoppingStreet';

/**
 * Central game composition root.
 *
 * Owns the renderer, the scene, the camera and the main loop. Feature
 * systems (player controller, collision, interaction, missions, ...) are
 * attached by later milestones and driven from {@link update}.
 */
export class Game {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene: THREE.Scene;
  readonly camera: THREE.PerspectiveCamera;
  readonly sceneManager: SceneManager;

  private readonly clock = new THREE.Clock();
  private rafId = 0;
  private running = false;
  private disposed = false;

  constructor(container: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
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
    this.camera.position.set(0, 1.7, 8);

    this.sceneManager = new SceneManager(this.scene, this.camera);

    // Milestone M3 replaces this placeholder street with the detailed
    // Japanese shopping street; the module keeps growing in place.
    this.sceneManager.add(new ShoppingStreet().group);

    window.addEventListener('resize', this.handleResize);
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
    window.removeEventListener('resize', this.handleResize);
    this.sceneManager.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }

  private loop = (): void => {
    if (!this.running) return;
    this.rafId = requestAnimationFrame(this.loop);
    const dt = Math.min(this.clock.getDelta(), 0.1);
    this.update(dt);
    this.renderer.render(this.scene, this.camera);
  };

  /**
   * Frame update hook. Milestones attach their systems by overriding or
   * extending this method.
   */
  protected update(_dt: number): void {
    // To be extended by movement, interaction and mission systems.
  }

  private readonly handleResize = (): void => {
    const width = this.renderer.domElement.clientWidth || window.innerWidth;
    const height = this.renderer.domElement.clientHeight || window.innerHeight;
    this.camera.aspect = width / Math.max(1, height);
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  };
}
