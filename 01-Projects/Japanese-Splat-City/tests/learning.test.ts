/**
 * M5 — vocabulary learning tests.
 *
 * Three layers, mirroring the M4 interaction tests:
 *
 * 1. Content contract (`src/content/vocabulary.ts`): the typed schema, the
 *    N4–N3 spread, and the fact that the content is keyed to the M4 registry —
 *    every one of the 12 interactables teaches at least one word, and no word
 *    points at an interactable that does not exist. The schema is also checked
 *    to have no quiz fields: M5 is discovery + notebook, not translation
 *    quizzes.
 * 2. `LearningSystem` (DOM-free): encounter tracking, discovery events,
 *    snapshot/restore round-trip and defensive restore.
 * 3. The M4 → M5 hook: the ids the registry hands to `recordEncounter` are the
 *    same ids the vocabulary is keyed by, so one interaction path feeds both.
 */

import { describe, expect, it, vi } from 'vitest';
import {
  VOCABULARY,
  VOCABULARY_BY_ID,
  VOCABULARY_LEVELS,
  vocabularyFor,
  vocabularyForLevel,
  type VocabularyEntry,
} from '../src/content/vocabulary';
import { LearningSystem } from '../src/systems/LearningSystem';
import { INTERACTABLES } from '../src/world/Interactives';

const JAPANESE = /[\u3040-\u30ff\u3400-\u9fff]/;

/** The exact schema of a vocabulary entry — no quiz prompt/choices/answer. */
const ENTRY_KEYS = [
  'id',
  'word',
  'reading',
  'meaning',
  'level',
  'pos',
  'example',
  'exampleMeaning',
  'interactableId',
].sort();

describe('M5 vocabulary content', () => {
  it('has a non-trivial N4–N3 word list with unique ids', () => {
    expect(VOCABULARY.length).toBeGreaterThanOrEqual(20);
    const ids = VOCABULARY.map((entry) => entry.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(VOCABULARY_BY_ID.size).toBe(VOCABULARY.length);
  });

  it('only uses the declared JLPT levels and covers both of them', () => {
    for (const entry of VOCABULARY) {
      expect(VOCABULARY_LEVELS).toContain(entry.level);
    }
    for (const level of VOCABULARY_LEVELS) {
      expect(vocabularyForLevel(level).length).toBeGreaterThan(0);
    }
    // N4 is the bulk of the content, N3 is the stretch tier.
    expect(vocabularyForLevel('N4').length).toBeGreaterThan(vocabularyForLevel('N3').length);
  });

  it('fills every field with real Japanese text', () => {
    for (const entry of VOCABULARY) {
      expect(entry.id).toMatch(/^v-[a-z-]+$/);
      expect(entry.word.length).toBeGreaterThan(0);
      expect(entry.reading.length).toBeGreaterThan(0);
      expect(entry.meaning.length).toBeGreaterThan(0);
      expect(entry.example.length).toBeGreaterThan(0);
      expect(entry.exampleMeaning.length).toBeGreaterThan(0);
      expect(entry.word).toMatch(JAPANESE);
      expect(entry.reading).toMatch(/[\u3040-\u30ff]/);
      expect(entry.example).toMatch(JAPANESE);
    }
  });

  it('has no quiz fields — discovery and notebook only', () => {
    for (const entry of VOCABULARY) {
      expect(Object.keys(entry).sort()).toEqual(ENTRY_KEYS);
    }
  });

  it('is keyed to the M4 registry: every interactable teaches a word', () => {
    const interactableIds = new Set(INTERACTABLES.map((def) => def.id));
    for (const def of INTERACTABLES) {
      expect(vocabularyFor(def.id).length).toBeGreaterThan(0);
    }
    for (const entry of VOCABULARY) {
      expect(interactableIds.has(entry.interactableId)).toBe(true);
    }
  });

  it('returns an empty list for unknown interactables', () => {
    expect(vocabularyFor('shop-does-not-exist')).toEqual([]);
  });
});

describe('LearningSystem', () => {
  it('starts empty and reports progress as a ratio', () => {
    const learning = new LearningSystem();
    expect(learning.total).toBe(VOCABULARY.length);
    expect(learning.discoveredCount).toBe(0);
    expect(learning.progress).toBe(0);
    expect(learning.discoveredEntries()).toEqual([]);
    expect(learning.undiscoveredEntries().length).toBe(VOCABULARY.length);
  });

  it('discovers every word taught by an interactable on first use', () => {
    const learning = new LearningSystem();
    const expected = vocabularyFor('shop-ramen-ya');
    const fresh = learning.recordEncounter('shop-ramen-ya', 1000);

    expect(fresh.map((entry) => entry.id)).toEqual(expected.map((entry) => entry.id));
    expect(learning.discoveredCount).toBe(expected.length);
    expect(learning.isDiscovered(expected[0].id)).toBe(true);
    expect(learning.encountersFor(expected[0].id)).toBe(1);
    expect(learning.progress).toBeCloseTo(expected.length / VOCABULARY.length, 10);
  });

  it('only bumps the counter on repeat encounters', () => {
    const learning = new LearningSystem();
    learning.recordEncounter('monument', 1000);
    const again = learning.recordEncounter('monument', 2000);

    expect(again).toEqual([]);
    expect(learning.discoveredCount).toBe(vocabularyFor('monument').length);
    for (const entry of vocabularyFor('monument')) {
      expect(learning.encountersFor(entry.id)).toBe(2);
    }
  });

  it('ignores unknown interactable ids', () => {
    const learning = new LearningSystem();
    expect(learning.recordEncounter('nope')).toEqual([]);
    expect(learning.discoveredCount).toBe(0);
    expect(learning.entriesFor('nope')).toEqual([]);
  });

  it('keeps discovered words in content order', () => {
    const learning = new LearningSystem();
    learning.recordEncounter('prop-apple', 1);
    learning.recordEncounter('shop-sento', 2);

    const discovered = learning.discoveredEntries().map((entry) => entry.id);
    const expected = VOCABULARY.filter((entry) => discovered.includes(entry.id)).map(
      (entry) => entry.id,
    );
    expect(discovered).toEqual(expected);
    expect(learning.undiscoveredEntries().length).toBe(
      VOCABULARY.length - learning.discoveredCount,
    );
  });

  it('emits one discovery event per fresh word and honours unsubscribe', () => {
    const learning = new LearningSystem();
    const listener = vi.fn();
    const unsubscribe = learning.subscribe(listener);

    learning.recordEncounter('shop-hon-ya', 500);
    expect(listener).toHaveBeenCalledTimes(vocabularyFor('shop-hon-ya').length);
    const first = listener.mock.calls[0][0] as { entry: VocabularyEntry; at: number };
    expect(first.at).toBe(500);
    expect(first.entry.interactableId).toBe('shop-hon-ya');

    // Repeats do not re-announce.
    learning.recordEncounter('shop-hon-ya', 600);
    expect(listener).toHaveBeenCalledTimes(vocabularyFor('shop-hon-ya').length);

    unsubscribe();
    learning.recordEncounter('shop-sento', 700);
    expect(listener).toHaveBeenCalledTimes(vocabularyFor('shop-hon-ya').length);
  });

  it('round-trips through snapshot/restore', () => {
    const learning = new LearningSystem();
    learning.recordEncounter('shop-wagashi', 111);
    learning.recordEncounter('shop-wagashi', 222);
    learning.recordEncounter('prop-concrete-cat-statue', 333);

    const snapshot = learning.snapshot();
    expect(snapshot.version).toBe(1);
    expect(Object.keys(snapshot.discovered)).toEqual(
      [...Object.keys(snapshot.discovered)].sort(),
    );

    const restored = new LearningSystem();
    restored.restore(snapshot);
    expect(restored.discoveredCount).toBe(learning.discoveredCount);
    expect(restored.snapshot()).toEqual(snapshot);
    for (const entry of vocabularyFor('shop-wagashi')) {
      expect(restored.encountersFor(entry.id)).toBe(2);
    }
  });

  it('rejects malformed snapshots instead of trusting them', () => {
    const learning = new LearningSystem();
    learning.recordEncounter('shop-kissaten', 1);

    learning.restore(null);
    expect(learning.discoveredCount).toBe(0);

    learning.restore({ version: 2 as unknown as 1, discovered: {} });
    expect(learning.discoveredCount).toBe(0);

    learning.restore({
      version: 1,
      discovered: {
        'v-not-real': { at: 1, encounters: 1 },
        'v-chumon': { at: Number.NaN, encounters: Number.NaN },
        'v-aji': { at: 5, encounters: 0 },
      },
    });
    expect(learning.isDiscovered('v-not-real')).toBe(false);
    expect(learning.encountersFor('v-chumon')).toBe(1);
    expect(learning.encountersFor('v-aji')).toBe(1);
  });

  it('resets progress but keeps listeners subscribed', () => {
    const learning = new LearningSystem();
    const listener = vi.fn();
    learning.subscribe(listener);
    learning.recordEncounter('shop-hana-ya', 1);
    learning.reset();

    expect(learning.discoveredCount).toBe(0);
    expect(learning.progress).toBe(0);

    learning.recordEncounter('shop-hana-ya', 2);
    expect(listener).toHaveBeenCalledTimes(vocabularyFor('shop-hana-ya').length * 2);
  });

  it('accepts an injected content set (keeps the system testable)', () => {
    const custom: VocabularyEntry[] = [
      {
        id: 'v-test',
        word: '試験',
        reading: 'しけん',
        meaning: 'test',
        level: 'N4',
        pos: 'noun',
        example: '試験があります。',
        exampleMeaning: 'There is a test.',
        interactableId: 'shop-test',
      },
    ];
    const learning = new LearningSystem(custom);
    expect(learning.total).toBe(1);
    expect(learning.recordEncounter('shop-test', 9).map((entry) => entry.id)).toEqual(['v-test']);
    expect(learning.progress).toBe(1);
  });
});
