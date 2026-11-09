# rasterize-jp-text.ps1
# Offline Japanese signage rasterizer for Japanese Splat City.
#
# Renders every sign text from the manifest TSV (UTF-8) using the Noto Sans CJK JP
# OTF via GDI+ PrivateFontCollection - no font install, no Unity editor required.
# Outputs one PNG per sign, one combined kanji-swatch proof sheet, and a
# signs-manifest.json recording generator, font SHA256, per-file SHA256.
# PNGs land under Assets/Resources/Textures/Signs so BlockBuilder can load them
# at runtime with Resources.Load (zero editor work on first import).
#
# Usage (PS 5.1, Windows 10+):
#   powershell -NoProfile -ExecutionPolicy Bypass -File rasterize-jp-text.ps1
# Optional: -FontPath <path> -ManifestPath <path> -OutDir <path>
#
# ASCII-only source: all non-ASCII text lives in the TSV manifest (UTF-8, read
# with explicit encoding) so PowerShell 5.1 never mis-decodes this script.
#
# Font: NOTO SANS CJK JP - SIL OFL 1.1 (see LICENSE/NotoSansJP/ in repo root).
# Textures are generated at build time from that licensed font; the bundled font
# + OFL + NOTICE ship with the packaged player.

param(
    [string]$FontPath   = (Join-Path (Split-Path $PSScriptRoot -Parent) '..\..\..\..\.tools\font-source\NotoSansCJKjp-Regular.otf'),
    [string]$ManifestPath = (Join-Path $PSScriptRoot 'sign-texts.tsv'),
    [string]$OutDir     = (Join-Path $PSScriptRoot '..\Assets\Resources\Textures\Signs'),
    [int]$CanvasH       = 128,
    [int]$FontSize      = 96,
    [int]$PadX          = 16,
    [int]$SwatchCell    = 96,
    [int]$SwatchCols    = 12
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

if (-not (Test-Path $FontPath)) { throw "Font not found: $FontPath" }
if (-not (Test-Path $ManifestPath)) { throw "Manifest not found: $ManifestPath" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# --- load font from file (no install) ---
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
try {
    $pfc.AddFontFile($FontPath)
} catch {
    throw "Failed to load OTF via PrivateFontCollection: $_"
}
$fam = New-Object System.Drawing.FontFamily($pfc.Families[0].Name, $pfc)
$font = New-Object System.Drawing.Font($fam, $FontSize, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)

function Parse-Hex([string]$hex, [byte]$a) {
    $hex = $hex.TrimStart('#')
    if ($hex.Length -ne 6) { throw "Bad color '$hex' (need RRGGBB)" }
    return [System.Drawing.Color]::FromArgb($a,
        [Convert]::ToByte($hex.Substring(0,2),16),
        [Convert]::ToByte($hex.Substring(2,2),16),
        [Convert]::ToByte($hex.Substring(4,2),16))
}

# --- read manifest (explicit UTF-8) ---
$text = [System.IO.File]::ReadAllText($ManifestPath, [System.Text.Encoding]::UTF8)
$entries = @()
$allChars = New-Object System.Collections.Generic.HashSet[char]
$lines = $text -split "`r?`n" | ForEach-Object { $_.TrimEnd("`r") }
$ln = 0
foreach ($line in $lines) {
    $ln++
    if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
    $cols = $line -split "`t"
    if ($cols.Count -lt 2) { throw "Manifest line ${ln}: expected 'tag<TAB>text[<TAB>width_hint[<TAB>fg[<TAB>bg]]]'" }
    $tag  = $cols[0].Trim()
    $s    = $cols[1]
    $w    = if ($cols.Count -gt 2 -and $cols[2].Trim().Length -gt 0) { [int]$cols[2] } else { 0 }
    $fgc  = if ($cols.Count -gt 3 -and $cols[3].Trim().Length -gt 0) { Parse-Hex $cols[3] 255 } else { [System.Drawing.Color]::FromArgb(255,242,239,233) }
    $bgc  = if ($cols.Count -gt 4 -and $cols[4].Trim().Length -gt 0) { Parse-Hex $cols[4] 255 } else { [System.Drawing.Color]::FromArgb(255,18,21,29) }
    $entries += ,[pscustomobject]@{ Tag=$tag; Text=$s; WidthHint=$w; Fg=$fgc; Bg=$bgc }
    foreach ($ch in $s.ToCharArray()) { [void]$allChars.Add($ch) }
}
if ($entries.Count -eq 0) { throw "Manifest has no entries" }

# --- per-sign render ---
$bitmap = New-Object System.Drawing.Bitmap(4, 4)
$measureG = [System.Drawing.Graphics]::FromImage($bitmap)
$measureG.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$record = @()
foreach ($e in $entries) {
    $sz = $measureG.MeasureString($e.Text, $font)
    $canvasW = [Math]::Max([int][Math]::Ceiling($sz.Width) + (2 * $PadX), $e.WidthHint)
    $canvasW = $canvasW + (4 - ($canvasW % 4)) % 4   # multiple of 4
    $bmp = New-Object System.Drawing.Bitmap($canvasW, $CanvasH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.Clear($e.Bg)
    $fgBrush = New-Object System.Drawing.SolidBrush($e.Fg)
    $y = ($CanvasH - $sz.Height) / 2.0
    $g.DrawString($e.Text, $font, $fgBrush, (($canvasW - $sz.Width) / 2.0), $y)
    $file = "sign-" + $e.Tag + ".png"
    $outPath = Join-Path $OutDir $file
    $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $h = (Get-FileHash $outPath -Algorithm SHA256).Hash
    $record += ,[pscustomobject]@{ Tag=$e.Tag; Text=$e.Text; File=$file; Sha256=$h; WidthPx=$canvasW; HeightPx=$CanvasH }
    Write-Host ("  [{0}] {1} ({2}x{3}) sha256 {4}" -f $e.Tag, $e.Text, $canvasW, $CanvasH, $h.Substring(0,16))
    $fgBrush.Dispose(); $g.Dispose(); $bmp.Dispose()
}

# --- kanji swatch proof sheet (every unique character) ---
$chars = @($allChars | Sort-Object)
$rows = [int][Math]::Ceiling($chars.Count / [double]$SwatchCols)
$sheet = New-Object System.Drawing.Bitmap(($SwatchCols * $SwatchCell), ($rows * $SwatchCell), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$sg = [System.Drawing.Graphics]::FromImage($sheet)
$sg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$sg.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$sg.Clear([System.Drawing.Color]::FromArgb(255,18,21,29))
$swFont = New-Object System.Drawing.Font($fam, 64, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$white = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255,242,239,233))
$i = 0
foreach ($ch in $chars) {
    $col = $i % $SwatchCols; $rowAt = [int][Math]::Floor($i / $SwatchCols)
    $cx = $col * $SwatchCell; $cy = $rowAt * $SwatchCell
    $csz = $sg.MeasureString([string]$ch, $swFont)
    $sg.DrawString([string]$ch, $swFont, $white, ($cx + ($SwatchCell - $csz.Width) / 2.0), ($cy + ($SwatchCell - $csz.Height) / 2.0))
    $i++
}
$swatchFile = "proof-kanji-sheet.png"
$sheet.Save((Join-Path $OutDir $swatchFile), [System.Drawing.Imaging.ImageFormat]::Png)
$swatchHash = (Get-FileHash (Join-Path $OutDir $swatchFile) -Algorithm SHA256).Hash
$swFont.Dispose(); $white.Dispose(); $sg.Dispose(); $sheet.Dispose()
$measureG.Dispose(); $bitmap.Dispose(); $font.Dispose(); $fam.Dispose(); $pfc.Dispose()

# --- manifest json ---
$fontHash = (Get-FileHash $FontPath -Algorithm SHA256).Hash
$json = [ordered]@{
    generator        = "rasterize-jp-text.ps1"
    generatedAtUtc   = (Get-Date).ToUniversalTime().ToString("o")
    fontFile         = (Split-Path $FontPath -Leaf)
    fontSha256       = $fontHash
    fontBytes        = (Get-Item $FontPath).Length
    signCount        = $entries.Count
    uniqueChars      = $chars.Count
    swatchSheet      = @{ File=$swatchFile; Sha256=$swatchHash; Cells=$SwatchCell; Cols=$SwatchCols }
    entries          = $record
}
$jsonPath = Join-Path $OutDir 'signs-manifest.json'
$json | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath -Encoding UTF8
Write-Host ("Wrote {0} signs + {1} to {2}" -f $entries.Count, $swatchFile, $OutDir)
Write-Host ("Manifest: {0}" -f $jsonPath)
Write-Host ("Font sha256: {0}" -f $fontHash)
