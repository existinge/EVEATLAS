# JPSv3 Agent Operating Contract
## Builder — DeepSeek Flash
1. Inspect repository and existing project before coding. Never claim an existing build without running it.
2. Pick one bounded milestone. Write acceptance criteria as executable checks before expanding scope.
3. Ship minimal playable code and a dev URL. Commit coherent increments. Run typecheck, lint, test, build, browser smoke.
4. Keep game loop isolated from UI. Declare events/action schema, gameplay state, deterministic objectives, versioned saves, dependencies and licenses.
5. No unrelated engine migrations, giant rewrites, invented APIs, third-party skill scripts, unlicensed assets, or insecure package execution.
6. When blocked >2 focused attempts, produce reproducible error + logs + simplest unblock request. Do not paper over failing tests.
7. Handoff: commit SHA, changed files, commands and results, actual browser screenshots/traces, known failures, next smallest task.

## Required test matrix
- App launches from clean checkout with documented commands and deterministic lockfile.
- Enter Game button focuses game; keyboard W/A/S/D moves; mouse look works with browser supported Pointer Lock; no page scroll when actively playing.
- Input releases on blur, visibility change, pointerlockchange/fullscreenchange; Esc can exit mode; no permanent stuck keys.
- Walls, shelves, and floor constrain avatar; products are interactable in reach only.
- Japanese mission text matches internal item IDs; wrong item feedback does not soft-lock quest; completed mission persists after reload.
- No runtime uncaught errors. Test browser with screenshots and Playwright assertions; record fps measurements.
- Reduced motion, pause, mute, readable Japanese fonts, no forced furigana.

## Promotion gates
Green: clean compile/build + unit tests + browser smoke + accessible runnable demo + Antigravity review.
Yellow: known noncritical defect documented with issue and owner.
Red: app won't launch, cannot move/interact, broken progression/save, corrupt assets, secret leakage, unlicensed dependencies.
Never mark a Red milestone complete. Supervisor approval does not replace user review for changing core design.

## Definition of Done
A human can open the application, play the objective to completion, refresh, and retain state. A design doc or screenshot alone is NOT Done.
