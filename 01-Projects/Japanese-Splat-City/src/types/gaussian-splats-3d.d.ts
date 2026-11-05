/**
 * Local type shim for `@mkkellogg/gaussian-splats-3d` (v0.4.7).
 *
 * The package ships no TypeScript declarations; this module-level shim
 * declares only the API surface this project uses, verified against the
 * shipped CommonJS build (`build/gaussian-splats-3d.module.js`):
 *
 * - `Viewer.update(renderer, camera)` is a TWO-argument method; in
 *   non-drop-in mode the arguments are ignored, but they are passed anyway.
 * - `Viewer.render()` / `Viewer.shouldRender()` / `forceRenderNextFrame()`
 *   are no-argument field functions on the instance.
 * - `addSplatScene(path, options)` expects PLAIN arrays/numbers for
 *   `position` / `rotation` / `scale` (they are fed to THREE
 *   `Vector3.fromArray` / `Quaternion.fromArray`), never THREE objects.
 * - The exported numeric enums: RenderMode { Always:0, OnChange:1, Never:2 },
 *   SceneRevealMode { Default:0, Gradual:1, Instant:2 },
 *   LogLevel { None:0, Error:1, Warning:2, Info:3, Debug:4 }.
 *
 * Only what we use is declared; the full export list of the package is much
 * larger (see `build/gaussian-splats-3d.module.js`).
 */

declare module '@mkkellogg/gaussian-splats-3d' {
  /** When to render: always, only when something changes, or never. */
  export const RenderMode: {
    /** Render every frame regardless of changes. */
    Always: 0;
    /** Render the first frame and whenever the camera or splats change. */
    OnChange: 1;
    /** Never render automatically (only manual render() calls). */
    Never: 2;
  };

  /** How a splat scene reveals itself after loading. */
  export const SceneRevealMode: {
    /** Loader decides (fade-in reveal). */
    Default: 0;
    /** Fade in gradually after loading. */
    Gradual: 1;
    /** Show immediately once loaded. */
    Instant: 2;
  };

  /** Verbosity of the viewer's console logging. */
  export const LogLevel: {
    None: 0;
    Error: 1;
    Warning: 2;
    Info: 3;
    Debug: 4;
  };

  /** Options accepted by {@link Viewer.addSplatScene}. */
  export interface SplatSceneOptions {
    /** World-space position; plain [x, y, z] array. */
    position?: number[];
    /** World-space rotation; plain [x, y, z] Euler array. */
    rotation?: number[];
    /** Uniform world-space scale (number) or [x, y, z] array. */
    scale?: number | number[];
    /** Alpha threshold for trimming low-opacity splats. */
    splatAlphaRemovalThreshold?: number;
    /** Show the loading UI for this scene. */
    showLoadingUI?: boolean;
    /** Explicit scene format (SceneFormat enum); auto-detected when omitted. */
    format?: number;
    /** Stream progressive render while this scene loads (KSplat/SPZ). */
    progressiveLoad?: boolean;
  }

  /**
   * Viewer bound to an external WebGLRenderer, camera, and (optionally)
   * threeScene. This project drives it manually each frame:
   * `viewer.update(state.renderer, state.camera)` + `viewer.render()`.
   */
  export class Viewer {
    constructor(options: {
      /** External renderer the viewer renders into. */
      renderer: unknown;
      /** External camera the viewer renders with. */
      camera: unknown;
      /**
       * An existing THREE.Scene rendered (with its visible children) behind
       * the splats on every render() call. We pass the game scene so the
       * street stays visible beneath the splat model.
       */
      threeScene?: unknown;
      /** Up vector for the viewer camera, [x, y, z]. */
      cameraUp?: number[];
      /** Fallback initial camera position, [x, y, z]. */
      initialCameraPosition?: number[];
      /** Fallback initial camera look-at, [x, y, z]. */
      initialCameraLookAt?: number[];
      /** RenderMode enum value (default OnChange). */
      renderMode?: number;
      /**
       * When false (our case) the viewer neither starts its own loop nor
       * updates its own state: the host must call update()/render().
       */
      selfDrivenMode?: boolean;
      /** Use the viewer's built-in orbit controls (we bring our own). */
      useBuiltInControls?: boolean;
      /**
       * Share a single memory-mapped splat buffer across workers. Must be
       * false when splat buffers are accessed outside the workers.
       */
      sharedMemoryForWorkers?: boolean;
      /** Show the built-in load-progress UI. */
      showLoadingUI?: boolean;
      /** LogLevel enum value. */
      logLevel?: number;
      /** SceneRevealMode enum value. */
      sceneRevealMode?: number;
      /** Optional external controls object the viewer can drive. */
      cameraControls?: unknown;
      /** Render continuously even when nothing changed. */
      dynamicMode?: boolean;
      /** Drop-in mode renders into its own camera/controls. */
      dropInMode?: boolean;
    });

    /**
     * Loads a splat scene from a URL or path. Throws if the viewer is
     * already loading/unloading or disposing/disposed. Not awaited here —
     * loading is non-blocking; the game keeps running while it finishes.
     */
    addSplatScene(path: string, options?: SplatSceneOptions): Promise<unknown>;

    /**
     * Per-frame update. In non-drop-in mode the renderer/camera arguments
     * are accepted but ignored; passed anyway for safety across versions.
     */
    update(renderer?: unknown, camera?: unknown): void;

    /** Renders the threeScene (when provided) and the splat mesh. */
    render(): void;

    /** True when this frame should be rendered under the current mode. */
    shouldRender(): boolean;

    /** Queue a render on the next frame even if nothing changed. */
    forceRenderNextFrame(): void;

    /** Marks the viewer as disposing/disposed (async teardown). */
    dispose(): Promise<void>;

    /** True while the viewer is disposing or already disposed. */
    isDisposingOrDisposed(): boolean;

    /** True while a splat scene is loading or unloading. */
    isLoadingOrUnloading(): boolean;

    /** Starts the self-driven loop (only meaningful in selfDrivenMode). */
    start(): void;

    /** Stops the self-driven loop (only meaningful in selfDrivenMode). */
    stop(): void;

    /** Runs one self-driven update+render tick (selfDrivenMode only). */
    selfDrivenUpdate(): void;

    /** Number of splat scenes currently loaded. */
    getSceneCount(): number;
  }
}
