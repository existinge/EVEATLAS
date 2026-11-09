# Japanese Splat City - one-command native build + offline run pipeline (Windows x64).
#
# Prerequisites (documented in the project's docs/):
#   - Pinned editor 6000.3.28f1 installed at $EditorRoot (defaults to .tools sandbox path)
#   - A valid Unity entitlement on the executing machine (LicensingClient must be able
#     to bootstrap; this host's binary-identity confinement blocks even a valid ULF)
#   - SHA-verified splat payload at $SplatSource (defaults to the .tools splat-source path)
#
# Pipeline:
#   [1/4] stage the splat payload from $SplatSource into Assets/StreamingAssets
#         (M1Anchor_train.ply, SHA256-verified; *.ply is gitignored so the 266 MB
#         binary never enters the repo). GaussianSplatData asset + WalkMain scene
#         are then authored by ProjectAuthor.cs on the first editor run.
#   [2/4] headless import (license check + package compile happen here)
#   [3/4] standalone Windows x64 build via PlayerBuilder.cs (URP scene gate)
#   [4/4] launch the packaged player offline, archive Player.log into $logDir
#
# Usage:
#   .\Build.ps1                       # stage splat -> import -> build -> launch player
#   .\Build.ps1 -ImportOnly           # stage splat + headless import/compile only
#   .\Build.ps1 -SkipRun              # build without launching the player
#   .\Build.ps1 -Resolution 1280x720  # override player window resolution
#   .\Build.ps1 -SplatSource <path>   # override the splat payload location
#
# Everything is written under $OutRoot (outside the repo): payload, logs, evidence.
param(
    [string]$EditorRoot = 'C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\unity-editor\6000.3.28f1\Editor',
    [string]$Project     = $PSScriptRoot,
    [string]$OutRoot     = 'C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\unity-build',
    [string]$SplatSource = 'C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\splat-source\Voxel51-gaussian_splatting-train-iteration30000.ply',
    [string]$Resolution  = '1920x1080',
    [switch]$ImportOnly,
    [switch]$SkipRun
)
$ErrorActionPreference = 'Stop'

$Unity = Join-Path $EditorRoot 'Unity.exe'
if (-not (Test-Path $Unity)) { throw "Editor not found: $Unity" }

$stamp   = Get-Date -Format 'yyyyMMdd-HHmmss'
$logDir  = Join-Path $OutRoot 'logs'
$payload = Join-Path $OutRoot 'JapaneseSplatCity'
New-Item -ItemType Directory -Force -Path $logDir, $payload | Out-Null

$importLog = Join-Path $logDir "import-$stamp.log"
$buildLog  = Join-Path $logDir "build-$stamp.log"

Write-Host "[1/4] staging splat payload into Assets/StreamingAssets"
$streaming = Join-Path $Project 'Assets\StreamingAssets'
New-Item -ItemType Directory -Force -Path $streaming | Out-Null
if (-not (Test-Path $SplatSource)) {
    Write-Host "ERR: splat source not found: $SplatSource (see docs/SPLAT_PROCUREMENT.md)"
    exit 1
}
$expectedSplatSha = 'A4C1906CE0256F5CB2255AA078D18B468DC01D8604F6EDA1AAF22B235147A7A1'
$actualSplatSha = (Get-FileHash -Algorithm SHA256 $SplatSource).Hash
if ($actualSplatSha -ne $expectedSplatSha) {
    Write-Host "ERR: splat SHA256 mismatch:`n  got      $actualSplatSha`n  expected $expectedSplatSha"
    exit 1
}
$splatDest = Join-Path $streaming 'M1Anchor_train.ply'
Copy-Item -Force $SplatSource $splatDest
Write-Host "Staged $splatDest ($((Get-Item $splatDest).Length) bytes, SHA256 verified)"

Write-Host "[2/4] headless import (license check + package compile + scene authoring happen here)"
& $Unity -batchmode -quit -nographics -projectPath $Project -logFile $importLog 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "IMPORT FAILED (exit $LASTEXITCODE). Tail of ${importLog}:"
    Get-Content $importLog -Tail 25 | Write-Host
    exit 1
}
if ($ImportOnly) { Write-Host "Import OK. Log: $importLog"; exit 0 }

Write-Host "[3/4] building standalone Windows x64 player"
$exe = Join-Path $payload 'JapaneseSplatCity.exe'
& $Unity -batchmode -quit -nographics -projectPath $Project `
    -executeMethod JapaneseSplatCity.Build.PlayerBuilder.Build `
    -outputPath $exe -logFile $buildLog 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "BUILD FAILED (exit $LASTEXITCODE). Tail of ${buildLog}:"
    Get-Content $buildLog -Tail 40 | Write-Host
    exit 1
}
$payloadFiles = Get-ChildItem $payload -Recurse -File
$totalKB = [math]::Round((($payloadFiles | Measure-Object Length -Sum).Sum / 1KB), 0)
Write-Host "PAYLOAD OK: $($payloadFiles.Count) files, ~${totalKB} KB at $payload"
$payloadFiles | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB)}} | Out-String | Write-Host
if ($SkipRun) { exit 0 }

Write-Host "[4/4] launching player offline (editor closed) with -force-d3d12"
$res = $Resolution -split 'x'
$p = Start-Process -FilePath $exe -WorkingDirectory $payload -ArgumentList @(
    '-screen-fullscreen','0',
    '-screen-width', $res[0],
    '-screen-height', $res[1],
    '-force-d3d12') -PassThru
Write-Host "player PID $($p.Id) started; waiting 25 s for scene + player log"
Start-Sleep -Seconds 25
if ($p.HasExited) {
    Write-Host "PLAYER EXITED EARLY (code $($p.ExitCode)). See $buildLog and the archived LocalLow Player.log."
    exit 1
}
$playerLog = Join-Path $env:LOCALAPPDATA 'LocalLow\EVEATLAS\JapaneseSplatCity\Player.log'
if (Test-Path $playerLog) {
    Write-Host "Player.log: $playerLog"
    Get-Content $playerLog -Tail 15 | Write-Host
    $savedLog = Join-Path $logDir "player-$stamp.log"
    Copy-Item -Force $playerLog $savedLog
    Write-Host "Player.log archived to $savedLog"
} else {
    Write-Host "No Player.log yet at $playerLog"
}
Write-Host "PLAYER RUNNING (PID $($p.Id)). Capture evidence frames now; then: Stop-Process -Id $($p.Id)"
