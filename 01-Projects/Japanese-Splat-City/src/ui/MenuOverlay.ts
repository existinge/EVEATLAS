/**
 * Start / pause menu overlay: play button, reset position, graphics quality
 * preset and a control cheat-sheet. Kept DOM-only so the game layer stays
 * renderer-independent.
 */

export type QualityPreset = 'low' | 'medium' | 'high';

export const QUALITY_PRESETS: ReadonlyArray<{ id: QualityPreset; label: string }> = [
  { id: 'low', label: '低 (Low)' },
  { id: 'medium', label: '中 (Medium)' },
  { id: 'high', label: '高 (High)' },
];

export interface MenuOverlayCallbacks {
  onPlay: () => void;
  onReset: () => void;
  onQuality: (q: QualityPreset) => void;
}

const CONTROLS = [
  ['W A S D', 'Move (移動)'],
  ['Mouse', 'Look (視点)'],
  ['Shift', 'Sprint (ダッシュ)'],
  ['Space', 'Jump (ジャンプ)'],
  ['Esc', 'Pause menu (メニュー)'],
  ['R', 'Reset position (リセット)'],
];

export class MenuOverlay {
  private readonly root: HTMLDivElement;
  private readonly title: HTMLHeadingElement;
  private readonly subtitle: HTMLParagraphElement;
  private readonly qualityRow: HTMLDivElement;

  constructor(
    private readonly container: HTMLElement,
    private readonly callbacks: MenuOverlayCallbacks,
    initialQuality: QualityPreset = 'high',
  ) {
    this.root = document.createElement('div');
    this.root.className = 'modal menu-overlay';

    const card = document.createElement('div');
    card.className = 'modal-card';

    this.title = document.createElement('h2');
    this.title.textContent = 'Japanese Splat City';

    this.subtitle = document.createElement('p');
    this.subtitle.className = 'overlay-subtitle';

    card.append(this.title, this.subtitle);

    const controls = document.createElement('ul');
    controls.className = 'control-list';
    for (const [keys, what] of CONTROLS) {
      const li = document.createElement('li');
      const kbd = document.createElement('span');
      kbd.className = 'keys';
      kbd.textContent = keys;
      const label = document.createElement('span');
      label.className = 'what';
      label.textContent = what;
      li.append(kbd, label);
      controls.appendChild(li);
    }
    card.appendChild(controls);

    // Graphics quality presets.
    this.qualityRow = document.createElement('div');
    this.qualityRow.className = 'quality-row';
    const qualLabel = document.createElement('span');
    qualLabel.className = 'quality-label';
    qualLabel.textContent = 'Graphics';
    this.qualityRow.appendChild(qualLabel);
    for (const preset of QUALITY_PRESETS) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.dataset.quality = preset.id;
      btn.className = 'secondary';
      btn.textContent = preset.label;
      btn.addEventListener('click', () => {
        this.setActiveQuality(preset.id);
        this.callbacks.onQuality(preset.id);
      });
      this.qualityRow.appendChild(btn);
    }
    card.appendChild(this.qualityRow);
    this.setActiveQuality(initialQuality);

    // Action buttons.
    const play = document.createElement('button');
    play.id = 'menu-play';
    play.textContent = 'Play — あそぶ';
    play.addEventListener('click', () => this.callbacks.onPlay());

    const reset = document.createElement('button');
    reset.id = 'menu-reset';
    reset.className = 'secondary';
    reset.textContent = 'Reset position (R)';
    reset.addEventListener('click', () => this.callbacks.onReset());

    const row = document.createElement('div');
    row.className = 'action-row';
    row.append(play, reset);
    card.appendChild(row);

    this.root.appendChild(card);
  }

  /** Shows the overlay, optionally with a pause heading. */
  show(paused: boolean): void {
    this.title.textContent = paused ? 'Paused — ポーズ' : 'Japanese Splat City';
    this.subtitle.textContent = paused
      ? 'Pointer lock released. Press Play to continue.'
      : 'Walk the street and find the shops. Click Play to grab the mouse.';
    this.root.classList.remove('hidden');
    this.container.appendChild(this.root);
  }

  hide(): void {
    this.root.classList.add('hidden');
    this.root.remove();
  }

  setActiveQuality(q: QualityPreset): void {
    for (const btn of Array.from(this.qualityRow.querySelectorAll<HTMLButtonElement>('button[data-quality]'))) {
      btn.classList.toggle('active', btn.dataset.quality === q);
    }
  }
}