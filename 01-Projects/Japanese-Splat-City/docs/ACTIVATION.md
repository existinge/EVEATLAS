# ACTIVATION — Unity Personal offline license for the native build

Canonical handoff for unblocking the Windows player build. The user's chosen path:
**provide a Unity Personal `.ulf` (from manual offline activation)**.

## What to produce (standard Unity manual-activation flow)

Do this once on any normal, unconfined machine (Unity Hub + editor, or even just the browser site):

1. **Generate the `.alf` request file.**
   - Easiest (standard): open Unity Hub → installs → click the gear on your editor → **Manage licenses →
     Add manual license → Save license request** → pick "Unity Version: 6000.3.x" → save `Unity_v2019.2.ulf`
     request as an `.alf` file. Any recent editor works; the request encodes this machine's hardware ID,
     which is what ties the eventual license to a machine.
   - CLI equivalent (if you prefer the exact binary pinned here):
     ```
     "C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\unity-editor\6000.3.28f1\Editor\Data\Resources\Licensing\Client\Unity.Licensing.Client.exe" \
       --generate-alf-request \
       --activation-product-name "Unity" \
       --activation-product-version "6000.3.28f1" \
       --activation-file-path "<output>\Unity_v6000.3.alf"
     ```
     (note: run this on the machine that will actually run Unity — the `.alf` binds to hardware.)

2. **Submit the `.alf` at** <https://license.unity3d.com/manual> **with a Unity ID** that has a current
   Unity Personal seat. The site returns a `Unity_v5.x.ulf` file to download (the same page that shows
   your existing Personal license).

3. **Place the `.ulf` where I can reach it.** Drop the file anywhere and tell me its path, OR put it in:
   ```
   C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\licensing\Unity_v5.x.ulf
   ```
   (this folder is outside the repo, so the entitlement artifact is never committed).

## What happens after the `.ulf` arrives

1. I install/place the `.ulf` at `%LOCALAPPDATA%\Unity\License\Unity_v5.x.ulf` (with our own file tooling,
   which CAN write the profile) and validate it:
   ```
   Unity.Licensing.Client.exe --license <path> --showAllEntitlements
   ```
2. Then I attempt the headless open/import and the CLI standalone build from `native/`.

## Honest caveat (confinement may still block even a valid `.ulf`)

The `UnsupportedException`/`UnauthorizedAccessException` we already captured
(`...\AppData\Local\Unity\ ... is denied` at `MinimalLockFileSink..ctor`) happens at the *logging
bootstrap* of the **third-party binary**, before any license logic — a harness-level, binary-identity
confinement that system binaries (`cmd`, `pwsh`) are not subject to. That same bootstrap is what the editor
and UPM node trip on. So:

- A valid `.ulf` is **necessary** to activate any editor build.
- It may **not be sufficient on this host** if that binary-level confinement still denies the Licensing
  Client / editor / UPM children their profile writes.
- If the client still fails at logging bootstrap with a good `.ulf` in place, I will report that result
  **empirically** — not claim a build we cannot run — and the residual `native/` project is a fully
  specified, ready-to-build drop: exact editor version, pinned URP 17.3.0, vendored GaussianSplatting,
  and exact CLI build commands, so it can be built on any machine that can run Unity.

## Every *.alf/.ulf remains out of the repo

Not committed. Not pasted into notes. Least-privilege by design.