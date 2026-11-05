/**
 * Keyboard + pointer-lock input layer for the first-person controller.
 *
 * Pure DOM glue: tracks pressed keys, accumulates pointer-lock mouse deltas
 * and surfaces edge-triggered actions (jump, reset). It never mutates game
 * state — the {@link Game} loop reads `PlayerInput` each frame.
 */
export class InputController {
  /** Set to true once the user opts into pointer lock; click relocks. */
  lockRequested = false;

  private readonly keys = new Set<string>();
  private deltaX = 0;
  private deltaY = 0;
  private jumpQueued = false;
  private interactQueued = false;
  private locked = false;

  private readonly onKeyDown = (e: KeyboardEvent): void => {
    if (e.repeat) return;
    const code = e.code;
    this.keys.add(code);
    if (code === 'Space') {
      e.preventDefault();
      this.jumpQueued = true;
    } else if (code === 'KeyE') {
      this.interactQueued = true;
    }
  };
  private readonly onKeyUp = (e: KeyboardEvent): void => {
    this.keys.delete(e.code);
  };
  private readonly onMouseMove = (e: MouseEvent): void => {
    if (!this.locked) return;
    this.deltaX += e.movementX;
    this.deltaY += e.movementY;
  };
  private readonly onPointerLockChange = (): void => {
    this.locked = document.pointerLockElement === this.target;
    document.body.classList.toggle('pointer-locked', this.locked);
  };
  private readonly onClick = (): void => {
    if (!this.locked) this.requestLock();
  };

  constructor(private readonly target: HTMLElement) {
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
    document.addEventListener('mousemove', this.onMouseMove);
    document.addEventListener('pointerlockchange', this.onPointerLockChange);
    target.addEventListener('click', this.onClick);
  }

  isLocked(): boolean {
    return this.locked;
  }

  requestLock(): void {
    this.lockRequested = true;
    void this.target.requestPointerLock();
  }

  exitLock(): void {
    if (document.pointerLockElement) document.exitPointerLock();
  }

  /** Consumes the accumulated mouse look deltas since the last frame. */
  pullLookDelta(): { x: number; y: number } {
    const d = { x: this.deltaX, y: this.deltaY };
    this.deltaX = 0;
    this.deltaY = 0;
    return d;
  }

  /** Consumes the edge-triggered jump flag. */
  consumeJump(): boolean {
    const j = this.jumpQueued;
    this.jumpQueued = false;
    return j;
  }

  /** Consumes the edge-triggered interact (E) flag. */
  consumeInteract(): boolean {
    const i = this.interactQueued;
    this.interactQueued = false;
    return i;
  }

  getPlayerInput(): { forward: boolean; back: boolean; left: boolean; right: boolean; sprint: boolean } {
    return {
      forward: this.keys.has('KeyW') || this.keys.has('ArrowUp'),
      back: this.keys.has('KeyS') || this.keys.has('ArrowDown'),
      left: this.keys.has('KeyA') || this.keys.has('ArrowLeft'),
      right: this.keys.has('KeyD') || this.keys.has('ArrowRight'),
      sprint: this.keys.has('ShiftLeft') || this.keys.has('ShiftRight'),
    };
  }

  dispose(): void {
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
    document.removeEventListener('mousemove', this.onMouseMove);
    document.removeEventListener('pointerlockchange', this.onPointerLockChange);
    this.target.removeEventListener('click', this.onClick);
  }
}