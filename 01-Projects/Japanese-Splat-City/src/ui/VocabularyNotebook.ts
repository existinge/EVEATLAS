/**
 * Milestone M5 — vocabulary notebook.
 *
 * A read-only overlay listing every word in the content set, grouped by JLPT
 * level. Discovered words show the word, reading, gloss and example sentence;
 * undiscovered words stay masked and only hint at the shop or object that
 * teaches them, so the notebook never spoils a word the player has not met.
 *
 * The notebook owns no state: it renders from {@link LearningSystem} each time
 * it opens, which keeps it correct after a reset or a future M7 restore.
 */

import { VOCABULARY_LEVELS, type VocabularyEntry } from '../content/vocabulary';
import type { LearningSystem } from '../systems/LearningSystem';
import { INTERACTABLES } from '../world/Interactives';

export interface VocabularyNotebookCallbacks {
  /** Called when the player closes the notebook (button or key). */
  onClose: () => void;
}

const INTERACTABLE_LABELS: ReadonlyMap<string, string> = new Map(
  INTERACTABLES.map((def) => [def.id, def.label]),
);

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export class VocabularyNotebook {
  private readonly root: HTMLDivElement;
  private readonly progressEl: HTMLParagraphElement;
  private readonly bodyEl: HTMLDivElement;
  private readonly learning: LearningSystem;
  private readonly callbacks: VocabularyNotebookCallbacks;
  private visible = false;

  constructor(
    container: HTMLElement,
    learning: LearningSystem,
    callbacks: VocabularyNotebookCallbacks,
  ) {
    this.learning = learning;
    this.callbacks = callbacks;

    this.root = document.createElement('div');
    this.root.id = 'vocabulary-notebook';
    this.root.className = 'modal notebook hidden';
    this.root.innerHTML = `
      <div class="modal-card">
        <h2>単語帳 — Vocabulary notebook</h2>
        <p class="notebook-progress"></p>
        <div class="notebook-body"></div>
        <div class="action-row">
          <button id="notebook-close" class="secondary" type="button">Close (N)</button>
        </div>
      </div>
    `;

    const progress = this.root.querySelector<HTMLParagraphElement>('.notebook-progress');
    const body = this.root.querySelector<HTMLDivElement>('.notebook-body');
    const close = this.root.querySelector<HTMLButtonElement>('#notebook-close');
    if (!progress || !body || !close) {
      throw new Error('VocabularyNotebook: expected .notebook-progress/.notebook-body/#notebook-close');
    }
    this.progressEl = progress;
    this.bodyEl = body;
    close.addEventListener('click', () => this.callbacks.onClose());

    container.appendChild(this.root);
  }

  isOpen(): boolean {
    return this.visible;
  }

  open(): void {
    if (this.visible) return;
    this.visible = true;
    this.render();
    this.root.classList.remove('hidden');
  }

  close(): void {
    if (!this.visible) return;
    this.visible = false;
    this.root.classList.add('hidden');
  }

  toggle(): void {
    if (this.visible) this.close();
    else this.open();
  }

  /** Re-renders the list from the current learning state. */
  render(): void {
    const discovered = this.learning.discoveredCount;
    const total = this.learning.total;
    this.progressEl.textContent = `${discovered} / ${total} words discovered — 見つけた単語`;

    const sections: string[] = [];
    for (const level of VOCABULARY_LEVELS) {
      const words = this.learning.all().filter((entry) => entry.level === level);
      if (words.length === 0) continue;
      const found = words.filter((entry) => this.learning.isDiscovered(entry.id)).length;
      sections.push(
        `<h3 class="vocab-level">${level}<span>${found} / ${words.length}</span></h3>`,
        `<ul class="vocab-list">${words.map((entry) => this.renderEntry(entry)).join('')}</ul>`,
      );
    }
    this.bodyEl.innerHTML = sections.join('');
  }

  dispose(): void {
    this.close();
    this.root.remove();
  }

  private renderEntry(entry: VocabularyEntry): string {
    if (!this.learning.isDiscovered(entry.id)) {
      const source = INTERACTABLE_LABELS.get(entry.interactableId) ?? entry.interactableId;
      return `
        <li class="vocab-entry locked">
          <div class="vocab-head">
            <span class="vocab-word">？？？</span>
            <span class="vocab-reading">${entry.level}</span>
          </div>
          <div class="vocab-meaning">${escapeHtml(source)} で 見つける</div>
        </li>
      `;
    }

    const encounters = this.learning.encountersFor(entry.id);
    return `
      <li class="vocab-entry">
        <div class="vocab-head">
          <span class="vocab-word">${escapeHtml(entry.word)}</span>
          <span class="vocab-reading">${escapeHtml(entry.reading)}</span>
          <span class="vocab-badge">×${encounters}</span>
        </div>
        <div class="vocab-meaning">${escapeHtml(entry.meaning)}</div>
        <p class="vocab-example">
          ${escapeHtml(entry.example)}
          <span class="vocab-example-meaning">${escapeHtml(entry.exampleMeaning)}</span>
        </p>
      </li>
    `;
  }
}
