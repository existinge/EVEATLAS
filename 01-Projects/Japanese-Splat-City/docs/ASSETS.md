# Asset sources & licenses

Every asset shipped in `public/assets/` must be listed here with its source and
license. Nothing is added unless redistribution is permitted; this project lives
in a public repository.

## Gaussian splat content

| Asset | Source | License | Status |
| ----- | ------ | ------- | ------ |
| `splats/carved-bull-head.ksplat` | Poly Haven, "Bull Head" by Tina; baked by Innerscene | CC0 | ✅ (M2) |
| `splats/m3/apple.ksplat` | DX.GL multi-view datasets (splats trained from Poly Haven CC0 models); converted by Innerscene | CC0 | ✅ (M3) |
| `splats/m3/brass-diya-lantern.splat` | Poly Haven, "Brass Diya Lantern" by Bhargav Kubal; baked by Innerscene | CC0 | ✅ (M3) |
| `splats/m3/concrete-cat-statue.splat` | Poly Haven, "Concrete Cat Statue" by Rico Cilliers, Riley Queen; baked by Innerscene | CC0 | ✅ (M3) |

## Textures, audio, fonts

| Asset | Source | License | Status |
| ----- | ------ | ------- | ------- |
| _(none yet)_ | – | – | – |

## Generated content

| Asset | Origin | Status |
| ----- | ------ | ------ |
| Street geometry (road, sidewalks, building boxes) | Procedural, this repo (`src/world/ShoppingStreet.ts`) | ✅ |

## Policy

- If a needed asset cannot be obtained under a permissive license (CC0, CC BY,
  MIT, public domain), the fallback is procedural geometry or a generated
  splat produced by this project, documented explicitly in this file.
- Licenses for vendored files must be kept alongside the files in
  `public/assets/licenses/`.
