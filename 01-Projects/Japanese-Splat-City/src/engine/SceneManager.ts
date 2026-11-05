import * as THREE from 'three';

/**
 * Owns the Three.js scene graph, environment lighting and fog.
 *
 * Milestone M3 adds the Japanese shopping street; milestone M2 attaches
 * Gaussian splat content. Everything environment-level lives here.
 */
export class SceneManager {
  readonly scene: THREE.Scene;
  readonly camera: THREE.PerspectiveCamera;

  private readonly hemi: THREE.HemisphereLight;
  private readonly sun: THREE.DirectionalLight;
  private readonly disposables: Array<{ dispose: () => void }> = [];

  constructor(scene: THREE.Scene, camera: THREE.PerspectiveCamera) {
    this.scene = scene;
    this.camera = camera;

    scene.background = new THREE.Color(0x9ec8e8);
    scene.fog = new THREE.Fog(0x9ec8e8, 30, 120);

    this.hemi = new THREE.HemisphereLight(0xffffff, 0x8a7f6a, 0.9);
    scene.add(this.hemi);

    this.sun = new THREE.DirectionalLight(0xfff2d9, 1.6);
    this.sun.position.set(24, 32, 12);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(1024, 1024);
    this.sun.shadow.camera.near = 1;
    this.sun.shadow.camera.far = 80;
    this.sun.shadow.camera.left = -35;
    this.sun.shadow.camera.right = 35;
    this.sun.shadow.camera.top = 35;
    this.sun.shadow.camera.bottom = -35;
    scene.add(this.sun);
  }

  /** Adds any object to the scene and tracks it for disposal. */
  add(object: THREE.Object3D): void {
    this.scene.add(object);
  }

  remove(object: THREE.Object3D): void {
    this.scene.remove(object);
  }

  trackDisposable(d: { dispose: () => void }): void {
    this.disposables.push(d);
  }

  dispose(): void {
    this.scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (mesh.geometry) mesh.geometry.dispose();
      const material = (mesh as THREE.Mesh).material as
        | THREE.Material
        | THREE.Material[]
        | undefined;
      if (Array.isArray(material)) {
        for (const m of material) m.dispose();
      } else if (material) {
        material.dispose();
      }
    });
    for (const d of this.disposables) d.dispose();
    this.disposables.length = 0;
  }
}
