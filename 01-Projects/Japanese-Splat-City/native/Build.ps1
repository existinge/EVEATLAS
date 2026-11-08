# Japanese Splat City - one-command native build + offline run pipeline (Windows x64).
#
# Prerequisites (documented in the project's docs/):
#   - Pinned editor 6000.3.28f1 installed at $EditorRoot (defaults to .tools sandbox path)
#   - A valid Unity entitlement on the executing machine (LicensingClient must be able
#     to bootstrap; this host's binary-identity confinement blocks even a valid ULF)
#   - Walk scene authored at Assets/Scenes/WalkMain.unity (via PlayerBuilder.cs)
#
# Usage:
#   .\Build.ps1                       # import -> build -> launch player (editor closed)
#   .\Build.ps1 -ImportOnly           # headless import + package compile only
#   .\Build.ps1 -SkipRun              # build without launching the player
#   .\Build.ps1 -Resolution 1280x720   # override player window resolution
#
# Everything is written under $OutRoot (outside the repo): payload, logs, evidence.
param(
    [string]$EditorRoot = 'C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\unity-editor\6000.3.28f1\Editor',
    [string]$Project     = $PSScriptRoot,
    [string]$OutRoot     = 'C:\Users\exist\Documents\deepseek-harness\default-workspace\.tools\unity-build',
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

Write-Host "[1/3] headless import (license check + package compile happen here)"
& $Unity -batchmode -quit -nographics -projectPath $Project -logFile $importLog 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "IMPORT FAILED (exit $LASTEXITCODE). Tail of ${importLog}:"
    Get-Content $importLog -Tail 25 | Write-Host
    exit 1
}
if ($ImportOnly) { Write-Host "Import OK. Log: $importLog"; exit 0 }

Write-Host "[2/3] building standalone Windows x64 player"
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

Write-Host "[3/3] launching player offline (editor closed) with -force-d3d12"
$res = $Resolution -split 'x'
$p = Start-Process -FilePath $exe -WorkingDirectory $payload -ArgumentList @(
    '-screen-fullscreen','0',
    '-screen-width', $res[0],
    '-screen-height', $res[1],
    '-force-d3d12') -PassThru
Write-Host "player PID $($p.Id) started; waiting 25 s for scene + player log"
Start-Sleep -Seconds 25
if ($p.HasExited) {
    Write-Host "PLAYER EXITED EARLY (code $($p.ExitCode)). See $buildLog and LocalLow Player.log."
    exit 1
}
$playerLog = Join-Path $env:LOCALAPPDATA 'LocalLow\EVEATLAS\JapaneseSplatCity\Player.log'
if (Test-Path $playerLog) {
    Write-Host "Player.log: $playerLog"
    Get-Content $playerLog -Tail 15 | Write-Host
} else {
    Write-Host "No Player.log yet at $playerLog"
}
Write-Host "PLAYER RUNNING (PID $($p.Id)). Capture evidence frames now; then: Stop-Process -Id $($p.Id)"
