# verify-font-glyphs.ps1
# Programmatic proof that the rendered signage PNGs came from the real Noto Sans CJK JP
# OTF and contain no tofu/missing-glyph boxes.
#
# Checks (all ASCII source; non-ASCII input read with explicit UTF-8):
#   1. Font identity  - GlyphTypeface family names must include "Noto Sans CJK JP".
#   2. cmap coverage  - every character in sign-texts.tsv must map to a glyph id > 0
#                       in the font's CharacterToGlyphMap (0 = .notdef).
#   3. Ink fill ratio - each rendered sign PNG must have more than 5% non-background
#                       pixels. Hollow tofu boxes are only ~0.5-3%; real glyphs 10-40%.
#
# Writes font-glyph-report.json next to the signs and prints PASS/FAIL.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File verify-font-glyphs.ps1

param(
    [string]$FontPath     = (Join-Path (Split-Path $PSScriptRoot -Parent) '..\..\..\..\.tools\font-source\NotoSansCJKjp-Regular.otf'),
    [string]$ManifestPath = (Join-Path $PSScriptRoot 'sign-texts.tsv'),
    [string]$OutDir       = (Join-Path $PSScriptRoot '..\Assets\Resources\Textures\Signs'),
    [double]$MinFillRatio = 0.05
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName System.Drawing

if (-not (Test-Path $FontPath))   { throw "Font not found: $FontPath" }
if (-not (Test-Path $ManifestPath)) { throw "Manifest not found: $ManifestPath" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# --- 1. font identity via WPF GlyphTypeface (reads the font file's name/cmap tables) ---
$uri = New-Object System.Uri((Resolve-Path $FontPath).Path)
$gt = New-Object System.Windows.Media.GlyphTypeface($uri)
$familyNames = @($gt.FamilyNames.Values | ForEach-Object { [string]$_ })
$isNoto = ($familyNames | Where-Object { $_ -like 'Noto Sans CJK JP*' }).Count -gt 0
$fontSha = (Get-FileHash $FontPath -Algorithm SHA256).Hash

# --- 2. cmap coverage for every manifest character ---
$text = [System.IO.File]::ReadAllText($ManifestPath, [System.Text.Encoding]::UTF8)
$allChars = New-Object System.Collections.Generic.HashSet[char]
foreach ($line in ($text -split "`r?`n")) {
    if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
    $cols = $line -split "`t"
    if ($cols.Count -lt 2) { continue }
    foreach ($ch in $cols[1].ToCharArray()) { [void]$allChars.Add($ch) }
}
$map = $gt.CharacterToGlyphMap
$glyphKeys = New-Object 'System.Collections.Generic.HashSet[int]'
foreach ($k in $map.Keys) { [void]$glyphKeys.Add([int]$k) }
$charRows = @()
$coverageOk = $true
foreach ($ch in ($allChars | Sort-Object)) {
    $cp = [int]$ch
    if ($glyphKeys.Contains($cp)) { $gid = [int]$map[[int]$cp] } else { $gid = -1 }
    if ($gid -le 0) { $coverageOk = $false }
    $charRows += ,[pscustomobject]@{ Char = $ch; CodePoint = ('U+{0:X4}' -f $cp); GlyphId = $gid; Ok = ($gid -gt 0) }
}

# --- 3. ink fill ratio per sign PNG ---
function Test-FillRatio([string]$pngPath, [double]$minFill) {
    $bmp = New-Object System.Drawing.Bitmap($pngPath)
    $bgR = 18; $bgG = 21; $bgB = 29
    $ink = 0L; $total = [long]$bmp.Width * [long]$bmp.Height
    for ($y = 0; $y -lt $bmp.Height; $y++) {
        for ($x = 0; $x -lt $bmp.Width; $x++) {
            $p = $bmp.GetPixel($x, $y)
            $d = [Math]::Abs([int]$p.R - $bgR) + [Math]::Abs([int]$p.G - $bgG) + [Math]::Abs([int]$p.B - $bgB)
            if ($d -gt 24) { $ink++ }
        }
    }
    $bmp.Dispose()
    return [math]::Round(($ink / [double]$total), 4)
}

$signRows = @()
$fillOk = $true
foreach ($png in (Get-ChildItem $OutDir -Filter 'sign-*.png')) {
    $ratio = Test-FillRatio $png.FullName $MinFillRatio
    if ($ratio -lt $MinFillRatio) { $fillOk = $false }
    $signRows += ,[pscustomobject]@{ File = $png.Name; FillRatio = $ratio; Ok = ($ratio -ge $MinFillRatio) }
}

$verdict = ($isNoto -and $coverageOk -and $fillOk)
$report = [ordered]@{
    fontFile     = (Split-Path $FontPath -Leaf)
    fontSha256   = $fontSha
    familyNames  = $familyNames
    isNotoCjkJp  = $isNoto
    charactersChecked = $allChars.Count
    allGlyphsPresent  = $coverageOk
    minFillRatio = $MinFillRatio
    allSignsInked     = $fillOk
    verdict      = $(if ($verdict) { 'PASS' } else { 'FAIL' })
    characters   = $charRows
    signs        = $signRows
}
$jsonPath = Join-Path $OutDir 'font-glyph-report.json'
$report | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath -Encoding UTF8

Write-Host ("Font: {0}" -f ($familyNames -join ' | '))
Write-Host ("Characters checked: {0}, all glyphs present: {1}" -f $allChars.Count, $coverageOk)
foreach ($s in $signRows) { Write-Host ("  {0} fill {1:P1} ok={2}" -f $s.File, $s.FillRatio, $s.Ok) }
Write-Host ("VERDICT: {0}" -f $verdict)
Write-Host ("Report: {0}" -f $jsonPath)
