/**
 * Milestone M4 — interaction HUD.
 *
 * Builds the street banner (`#hud`), the target reticle (`#target-reticle`) and
 * the contextual interaction panel (`#interaction-panel`), all styled by the
 * existing rules in `src/styles/main.css` (no new CSS). Mounts into the
 * container passed to `Game` (`#app`) — the game has no other DOM root.
 *
 * Behaviour:
 * - While no object is targeted, the panel is hidden and the reticle is plain
 *   white; settings a target marks the reticle `.active` and shows the
 *   Japanese label, description and E-hint.
 * - After an E interaction, the panel swaps to the action message for a few
 *   seconds, then returns to the live prompt.
 * - M5 adds a small `#discovery-toast` above the reticle that announces the
 *   words a first-time interaction just added to the notebook.
 */

import type { InteractiveDef } from '../interaction/Interaction';

/** How long an action message stays visible before the prompt returns (ms). */
export const INTERACTION_MESSAGE_MS = 3200;

export class InteractionHud {
  private readonly hud: HTMLDivElement;
  private readonly reticle: HTMLDivElement;
  private readonly panel: HTMLDivElement;
  private readonly toast: HTMLDivElement;
  private readonly word: HTMLSpanElement;
  private readonly desc: HTMLParagraphElement;
  private readonly hint: HTMLParagraphElement;
  private current: InteractiveDef | null = null;
  private messageTimer: number | null = null;
  private toastTimer: number | null = null;

  constructor(container: HTMLElement) {
    this.hud = document.createElement('div');
    this.hud.id = 'hud';
    this.hud.innerHTML = `
      <div class="panel">
        <div class="hud-title">商店街 — Shōtengai</div>
        <div class="hud-sub">E で 調べる / N で 単語帳</div>
      </div>
    `;
    container.appendChild(this.hud);

    this.reticle = document.createElement('div');
    this.reticle.id = 'target-reticle';
    container.appendChild(this.reticle);

    this.panel = document.createElement('div');
    this.panel.id = 'interaction-panel';
    this.panel.className = 'hidden';
    this.panel.innerHTML = `
      <div>
        <span class="jp-word"></span>
      </div>
      <p class="jp-desc"></p>
      <p class="hint"></p>
    `;
    container.appendChild(this.panel);

    const word = this.panel.querySelector<HTMLSpanElement>('.jp-word');
    const desc = this.panel.querySelector<HTMLParagraphElement>('.jp-desc');
    const hint = this.panel.querySelector<HTMLParagraphElement>('.hint');
    if (!word || !desc || !hint) {
      throw new Error('InteractionHud: expected .jp-word/.jp-desc/.hint in #interaction-panel');
    }
    this.word = word;
    this.desc = desc;
    this.hint = hint;

    this.toast = document.createElement('div');
    this.toast.id = 'discovery-toast';
    this.toast.className = 'hidden';
    container.appendChild(this.toast);
  }

  /**
   * Drives the reticle + prompt from the currently targeted def (or null).
   * Uses an identity guard so a per-frame no-op costs nothing.
   */
  setPrompt(def: InteractiveDef | null): void {
    if (def === this.current) return;
    this.current = def;
    if (this.messageTimer !== null) return; // an action message is showing
    this.renderPrompt();
  }

  /** Shows a transient action message; the live prompt returns afterwards. */
  showMessage(text: string): void {
    if (this.messageTimer !== null) window.clearTimeout(this.messageTimer);
    this.messageTimer = window.setTimeout(() => {
      this.messageTimer = null;
      this.renderPrompt();
    }, INTERACTION_MESSAGE_MS);
    this.panel.classList.remove('hidden');
    this.word.textContent = '';
    this.desc.textContent = text;
    this.hint.textContent = '';
  }

  /**
   * Announces newly discovered words (M5). No-op for an empty list, so the
   * caller can pass the result of `LearningSystem.recordEncounter` directly.
   */
  showDiscovery(words: readonly string[]): void {
    if (words.length === 0) return;
    if (this.toastTimer !== null) window.clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(() => {
      this.toastTimer = null;
      this.toast.classList.add('hidden');
    }, INTERACTION_MESSAGE_MS);
    this.toast.textContent = `新しい単語 +${words.length} — ${words.join('・')}`;
    this.toast.classList.remove('hidden');
  }

  /** Dismisses everything immediately (used when pointer lock is released). */
  clear(): void {
    if (this.messageTimer !== null) window.clearTimeout(this.messageTimer);
    this.messageTimer = null;
    if (this.toastTimer !== null) window.clearTimeout(this.toastTimer);
    this.toastTimer = null;
    this.toast.classList.add('hidden');
    this.current = null;
    this.reticle.classList.remove('active');
    this.panel.classList.add('hidden');
  }

  dispose(): void {
    if (this.messageTimer !== null) window.clearTimeout(this.messageTimer);
    this.messageTimer = null;
    if (this.toastTimer !== null) window.clearTimeout(this.toastTimer);
    this.toastTimer = null;
    this.hud.remove();
    this.reticle.remove();
    this.panel.remove();
    this.toast.remove();
  }

  private renderPrompt(): void {
    const def = this.current;
    this.reticle.classList.toggle('active', def !== null);
    this.panel.classList.toggle('hidden', def === null);
    if (def) {
      this.word.textContent = def.label;
      this.desc.textContent = def.description;
      this.hint.textContent = `E — ${def.action}`;
    }
  }
}
