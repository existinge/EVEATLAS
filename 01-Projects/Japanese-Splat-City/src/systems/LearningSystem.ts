/**
 * Milestone M5 — learning system.
 *
 * Tracks which vocabulary the player has encountered and how often. DOM-free
 * and renderer-free on purpose: the notebook UI and the game loop both read
 * from this class, and the tests drive it directly in Node.
 *
 * The system is fed by the M4 interaction registry: when an interaction
 * succeeds, {@link Game} calls {@link LearningSystem.recordEncounter} with the
 * interactable id, and every word attached to that interactable is marked as
 * encountered. There is no second registry and no separate discovery path.
 *
 * Persistence is deliberately *not* here — M7 owns `localStorage`. This class
 * only exposes {@link LearningSystem.snapshot} / {@link LearningSystem.restore}
 * so M7 can serialise it under the single namespaced progress key.
 */

import { VOCABULARY, type VocabularyEntry } from '../content/vocabulary';

/** Emitted once per word the first time it is encountered. */
export interface DiscoveryEvent {
  /** The word that was just discovered. */
  entry: VocabularyEntry;
  /** `Date.now()` timestamp of the discovery. */
  at: number;
  /** How many times its source interactable has been used, including this one. */
  encounters: number;
}

/** Serialisable progress for one word. */
export interface WordProgress {
  /** `Date.now()` timestamp of the first encounter. */
  at: number;
  /** Number of times the source interactable has been used. */
  encounters: number;
}

/** Serialisable learning progress (M7 persists this verbatim). */
export interface LearningSnapshot {
  version: 1;
  /** Vocabulary id -> progress. Unknown ids are ignored on restore. */
  discovered: Record<string, WordProgress>;
}

export type DiscoveryListener = (event: DiscoveryEvent) => void;

const SNAPSHOT_VERSION = 1;

/**
 * Encountered-word tracking for the M5 vocabulary.
 *
 * A word is "discovered" the first time its interactable is used; later uses
 * only bump the encounter counter. Discovery is monotonic — there is no
 * un-discover, only {@link LearningSystem.reset}.
 */
export class LearningSystem {
  private readonly entries: readonly VocabularyEntry[];
  private readonly byId = new Map<string, VocabularyEntry>();
  private readonly byInteractable = new Map<string, VocabularyEntry[]>();
  private readonly discovered = new Map<string, WordProgress>();
  private readonly listeners = new Set<DiscoveryListener>();

  constructor(entries: readonly VocabularyEntry[] = VOCABULARY) {
    this.entries = entries;
    for (const entry of entries) {
      this.byId.set(entry.id, entry);
      const bucket = this.byInteractable.get(entry.interactableId);
      if (bucket) bucket.push(entry);
      else this.byInteractable.set(entry.interactableId, [entry]);
    }
  }

  /** Every word in the content set, in content order. */
  all(): readonly VocabularyEntry[] {
    return this.entries;
  }

  /** Total number of words in the content set. */
  get total(): number {
    return this.entries.length;
  }

  /** Number of words discovered so far. */
  get discoveredCount(): number {
    return this.discovered.size;
  }

  /** Discovery ratio in `[0, 1]` (`0` when the content set is empty). */
  get progress(): number {
    return this.total === 0 ? 0 : this.discovered.size / this.total;
  }

  /** The word with this id, or `undefined`. */
  entry(id: string): VocabularyEntry | undefined {
    return this.byId.get(id);
  }

  /** Whether the word with this id has been discovered. */
  isDiscovered(id: string): boolean {
    return this.discovered.has(id);
  }

  /** Encounter count for one word (`0` if never encountered). */
  encountersFor(id: string): number {
    return this.discovered.get(id)?.encounters ?? 0;
  }

  /** Every word taught by one interactable, discovered or not. */
  entriesFor(interactableId: string): readonly VocabularyEntry[] {
    return this.byInteractable.get(interactableId) ?? [];
  }

  /** Discovered words, in content order. */
  discoveredEntries(): VocabularyEntry[] {
    return this.entries.filter((entry) => this.discovered.has(entry.id));
  }

  /** Not-yet-discovered words, in content order. */
  undiscoveredEntries(): VocabularyEntry[] {
    return this.entries.filter((entry) => !this.discovered.has(entry.id));
  }

  /**
   * Records one use of an interactable.
   *
   * Every word attached to `interactableId` gets its encounter counter bumped;
   * words seen for the first time are returned (and announced to listeners) in
   * content order. Unknown ids are a no-op that returns `[]`.
   */
  recordEncounter(interactableId: string, now: number = Date.now()): VocabularyEntry[] {
    const words = this.byInteractable.get(interactableId);
    if (!words || words.length === 0) return [];

    const fresh: VocabularyEntry[] = [];
    for (const entry of words) {
      const previous = this.discovered.get(entry.id);
      if (previous) {
        previous.encounters += 1;
      } else {
        this.discovered.set(entry.id, { at: now, encounters: 1 });
        fresh.push(entry);
      }
    }

    for (const entry of fresh) {
      const progress = this.discovered.get(entry.id);
      if (!progress) continue;
      const event: DiscoveryEvent = {
        entry,
        at: progress.at,
        encounters: progress.encounters,
      };
      for (const listener of this.listeners) listener(event);
    }

    return fresh;
  }

  /** Subscribes to discovery events; returns an unsubscribe function. */
  subscribe(listener: DiscoveryListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  /** Serialisable copy of the current progress (deterministic key order). */
  snapshot(): LearningSnapshot {
    const discovered: Record<string, WordProgress> = {};
    for (const id of [...this.discovered.keys()].sort()) {
      const progress = this.discovered.get(id);
      if (progress) discovered[id] = { at: progress.at, encounters: progress.encounters };
    }
    return { version: SNAPSHOT_VERSION, discovered };
  }

  /**
   * Replaces the current progress with a snapshot. Unknown ids and malformed
   * numbers are dropped rather than trusted, so a stale or hand-edited save
   * cannot corrupt the counters.
   */
  restore(snapshot: LearningSnapshot | null | undefined): void {
    this.discovered.clear();
    if (!snapshot || snapshot.version !== SNAPSHOT_VERSION) return;
    for (const [id, progress] of Object.entries(snapshot.discovered ?? {})) {
      if (!this.byId.has(id) || !progress) continue;
      const at = Number.isFinite(progress.at) ? progress.at : 0;
      const encounters = Number.isFinite(progress.encounters)
        ? Math.max(1, Math.floor(progress.encounters))
        : 1;
      this.discovered.set(id, { at, encounters });
    }
  }

  /** Forgets all progress. Listeners stay subscribed. */
  reset(): void {
    this.discovered.clear();
  }
}
