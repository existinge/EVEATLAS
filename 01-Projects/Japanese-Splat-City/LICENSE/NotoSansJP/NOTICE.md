# NOTICE — Noto Sans CJK JP (Japanese signage font)

| Field | Value |
|---|---|
| Asset | Noto Sans CJK JP Regular (OTF) — `NotoSansCJKjp-Regular.otf` |
| License | **SIL Open Font License 1.1** (full text: `OFL-1.1.txt` in this folder) |
| Source | https://github.com/notofonts/noto-cjk (`Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf`) |
| Download date | 2026-11-08 (offline pre-stage, round 5) |
| SHA256 (OTF) | `68A3FC98800B2A27B371F2FB79991DAF3633BD89309D4FFAA6946FD587F375B5` (16 467 736 B) |
| SHA256 (OFL) | `6A73F9541C2DE74158C0E7CF6B0A58EF774F5A780BF191F2D7EC9CC53EFE2BF2` (4 301 B, verified identical to the copy in this folder) |
| Payload location | `.tools/font-source/` (workspace root, **outside git**) |
| Author / project | Google / Adobe — Noto CJK fonts project (https://github.com/notofonts/noto-cjk) |

## Why this font

Japanese signage (hiragana / katakana / kanji) is rasterized from this font by
`native/Tools/rasterize-jp-text.ps1` (TBD when the editor exists) — no screenshots of
proprietary assets, per `docs/ASSET_PROVENANCE.md` rule 2.

## License obligations (SIL OFL 1.1)

- Font may be used, modified, and **bundled in the packaged game** (OFL is not
  copyleft for use as a font in products).
- The OFL text must accompany the font wherever it is distributed.
- No claim of authorship of the font itself.
- Modified versions must not use the reserved font name "Noto".

## Compliance in this repository / package

- OFL 1.1 full text: `LICENSE/NotoSansJP/OFL-1.1.txt` (committed).
- This NOTICE is committed.
- The packaged player ships the font file + OFL + this NOTICE next to the executable
  (installer/package step, applied when the first packaged build is made).
- Game credits ("credits.txt" next to the executable) name the Noto CJK project.

## In-game credit line (planned)

> Japanese signage typeface: Noto Sans CJK JP © Google/Adobe, licensed under the
> SIL Open Font License 1.1.
