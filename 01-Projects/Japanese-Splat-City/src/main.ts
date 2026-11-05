import './styles/main.css';
import { Game } from './engine/Game';

function showFatalError(err: unknown): void {
  const message = err instanceof Error ? err.message : String(err);
  const app = document.getElementById('app');
  const overlay = document.createElement('div');
  overlay.className = 'fatal-error';
  overlay.innerHTML = `
    <h1>起動に失敗しました / Failed to start</h1>
    <p>${message.replace(/</g, '&lt;')}</p>
    <p>This demo needs a browser with WebGL support.</p>
  `;
  if (app) app.appendChild(overlay);
  console.error(err);
}

async function bootstrap(): Promise<void> {
  const app = document.getElementById('app');
  if (!app) throw new Error('Missing #app container element.');

  try {
    const game = new Game(app);
    game.renderOnce();

    // Expose a small debug handle in the console (dev convenience only).
    (window as unknown as { __splatCityGame?: Game }).__splatCityGame = game;

    game.start();
  } catch (err) {
    showFatalError(err);
  }
}

void bootstrap();
