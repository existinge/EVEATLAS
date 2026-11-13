# PowerShell wrapper around Ghidra analyzeHeadless for the diff pipeline.
# Usage:
#   ./scripts/ghidra/run_headless.ps1 -Bin firmware/extracted/r7/tz.mbn -Rev r7 -Comp tz -OutDir analysis/export
param(
  [Parameter(Mandatory=$true)][string]$Bin,
  [Parameter(Mandatory=$true)][string]$Rev,
  [Parameter(Mandatory=$true)][string]$Comp,
  [string]$OutDir = "analysis/export",
  [string]$GhidraHome = $env:GHIDRA_HOME
)

if (-not $GhidraHome -or -not (Test-Path $GhidraHome)) {
  Write-Error "GHIDRA_HOME not set or invalid: '$GhidraHome'"
  exit 1
}

$Out = Join-Path (Get-Location) $OutDir
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$OutJson = Join-Path $Out "$Comp`-$Rev.json"
$Proj = Join-Path $Out "$Comp-proj"
$Script = Join-Path (Get-Location) "scripts/ghidra/ExportFunctions.java"

$analyze = Join-Path $GhidraHome "support/analyzeHeadless.bat"
& $analyze $Proj $Comp -import $Bin -postScript $Script $OutJson $Rev
Write-Host "export -> $OutJson (exit $LASTEXITCODE)"
exit $LASTEXITCODE