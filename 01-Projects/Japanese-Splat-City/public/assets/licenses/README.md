# Asset licenses

All assets in this directory tree are documented in [docs/ASSETS.md](../../docs/ASSETS.md).
Nothing in here may be redistributed unless its license permits it.

## Splats

### `splats/carved-bull-head.ksplat`

- **Asset:** "Carved bull head" — a decorative wall-mounted bull head sculpture with
  long horns, baked as a Gaussian splat (`.ksplat`, ~4.6 MB).
- **License:** [Public domain (CC0)](https://creativecommons.org/publicdomain/zero/1.0/) —
  free to use, modify and redistribute for any purpose, including commercially, with
  no credit required (credit is given anyway, out of gratitude).
- **Source model:** [Poly Haven, "Bull Head" by Tina](https://polyhaven.com/a/bull_head) (CC0).
- **Splat baked by:** [Innerscene](https://www.innerscene.com/) 3D Viewer splat export
  (ray-traced views). Downloaded from
  `https://www.innerscene.com/api/library/carved-bull-head-ksplat-46b87b58/download`.
- **View in 3D:** https://www.innerscene.com/v/6Dtt14ltI7ENmLBO2BFFAJ
- **Used in game as:** the street monument outside the shop (see
  `src/world/ShoppingStreet.ts`, `MONUMENT`) — rendered visually only; gameplay
  collision uses a matching axis-aligned box in `src/world/Colliders.ts`.
