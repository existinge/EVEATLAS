/**
 * Milestone M4 — interaction registry.
 *
 * Owns the interactable-def list, ray targeting, the E-interaction cooldown
 * and the recent-interaction history. Pure logic (no DOM, no Three.js): the
 * only "splats-aware" part of M4 is that the defs' boxes were derived from
 * the world geometry in {@link ../world/Interactives}.
 *
 * The registry is the single interaction+data hook for M4 and M5: milestone
 * M5 (vocabulary learning) consumes {@link InteractiveDef} entries through
 * {@link InteractiveRegistry.all} without adding a second data path.
 */

import {
  interactionTarget,
  type InteractiveDef,
  type Vec3Like,
} from './Interaction';

export interface InteractionHistoryEntry {
  /** Def id that was interacted with. */
  id: string;
  /** Japanese label at interaction time (snapshot, stable in practice). */
  label: string;
  /** The action message that was shown. */
  message: string;
  /** Epoch ms of the interaction. */
  at: number;
}

export class InteractiveRegistry {
  private readonly defs: readonly InteractiveDef[];
  private readonly byId = new Map<string, InteractiveDef>();
  /** id -> epoch ms of the last successful interaction (cooldown). */
  private readonly lastInteracted = new Map<string, number>();
  /** Most recent first; capped at historyLimit. */
  private readonly history: InteractionHistoryEntry[] = [];

  constructor(
    defs: readonly InteractiveDef[],
    private readonly cooldownMs: number = 1200,
    private readonly historyLimit: number = 12,
  ) {
    this.defs = defs;
    for (const def of defs) this.byId.set(def.id, def);
  }

  /** All interactables, in definition order. */
  all(): readonly InteractiveDef[] {
    return this.defs;
  }

  get(id: string): InteractiveDef | undefined {
    return this.byId.get(id);
  }

  /** Number of registered interactables. */
  get size(): number {
    return this.byId.size;
  }

  /**
   * Nearest interactable hit by the ray from `origin` along `dir` within
   * `maxDistance`, or null. Delegates to pure math (unit-testable).
   */
  target(
    origin: Vec3Like,
    dir: Vec3Like,
    maxDistance: number,
  ): InteractiveDef | null {
    return interactionTarget(this.defs, origin, dir, maxDistance);
  }

  /**
   * Performs an interaction on the given def id: records it in the history
   * and returns the history entry, or null when the id is unknown or still
   * inside the per-def cooldown (prevents E-spam bookmarking the log).
   */
  interact(id: string): InteractionHistoryEntry | null {
    const def = this.byId.get(id);
    if (!def) return null;
    const now = Date.now();
    const last = this.lastInteracted.get(id) ?? -Infinity;
    if (now - last < this.cooldownMs) return null;
    this.lastInteracted.set(id, now);

    const entry: InteractionHistoryEntry = {
      id,
      label: def.label,
      message: def.message,
      at: now,
    };
    this.history.unshift(entry);
    if (this.history.length > this.historyLimit) {
      this.history.length = this.historyLimit;
    }
    return entry;
  }

  /** Recent interactions, most recent first. */
  historySnapshot(): readonly InteractionHistoryEntry[] {
    return this.history;
  }
}
