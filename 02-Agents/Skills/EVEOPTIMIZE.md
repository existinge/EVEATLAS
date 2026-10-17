---
name: eveoptimize
description: >-
  EVEOPTIMIZE: Portable, agent-executable competitive PC gaming optimization tuner,
  Source 2 (Deadlock/CS2) & Unreal Engine (Valorant/Marvel Rivals) runbook, Process Lasso
  core-isolation engine, BIOS/OS latency checklist, and discreet live match telemetry
  profiler. Drop this file into any coding agent to audit, tune, and benchmark any Windows gaming PC.
---

# Skill: EVEOPTIMIZE — Competitive PC & Source 2 Optimization Tuner

See [[02-Agents/Agent Registry]], [[02-Agents/Skills/experiment-design]], [[02-Agents/Skills/context-handoff]].

**Purpose:** Enable any autonomous coding agent (Antigravity, Claude Code, Cursor, OpenClaw) to perform a deterministic, hardware-aware end-to-end gaming optimization and live match telemetry audit on a Windows PC—without hardcoded paths, blind placebo tweaks, or breaking anti-cheat / mod managers.

---

## 1. Core Engineering Rules (Non-Negotiable)

1. **Never Starve Games of Physical Cores in Process Lasso:**
   - Never restrict a modern game (`deadlock.exe`, `valorant-win64-shipping.exe`, `overwatch.exe`, `cs2.exe`) to a subset of cores on a single-CCD CPU (e.g., locking an 8-core/16-thread CPU to `0–11` / `0xFFF`). Doing so cuts off physical cores and forces game worker threads onto SMT sibling hyperthreads where they contend with the Main and Render threads.
   - **Correct Rule:** Dynamically query total logical threads $T$ (`0` to $T-1$). Grant games **all threads (`0..(T-1)`)** at `High` priority, and quarantine background Chromium/overlay helpers (`discord.exe`, `steamwebhelper.exe`, `epicwebhelper.exe`, `blizzardbrowser.exe`, `leagueclientuxrender.exe`) to the **last physical core (`(T-2)-(T-1)`)** at **`Below Normal`** priority.
2. **Always Target the Real Shipping Binary (Not Just the Launcher):**
   - Unreal Engine games run inside a child shipping binary:
     - Valorant: `VALORANT-Win64-Shipping.exe` (launcher is `VALORANT.exe`)
     - Marvel Rivals: `Marvel-Win64-Shipping.exe` (launcher is `Marvel.exe`)
   - Always register both the launcher and the `-Win64-Shipping.exe` binary in Process Lasso, Windows Kernel `PerfOptions`, and DirectX `UserGpuPreferences`.
3. **Source 2 (`Deadlock` / `CS2`) Specific Invariants:**
   - **Never add `-no_prewarm_map`** to Steam Launch Options—skipping map asset prewarming causes severe (~100 FPS) shader/particle compilation stalls on the first ability cast of every teamfight.
   - **Set `-threads <PhysicalCores + 1>`** (e.g., `-threads 9` on an 8-core CPU) so Source 2 allocates 1 main thread + 1 worker per physical core without saturating SMT siblings.
   - **Never save `gameinfo.gi` with a UTF-8 BOM (`EF BB BF`)**—Source 2's `KeyValues` parser and Deadlock Mod Manager (DMM) fail if a 3-byte BOM is present. Always write using `New-Object System.Text.UTF8Encoding($false)`.

---

## 2. Phase 1: Dynamic Hardware & OS Discovery (Run First)

The agent must execute this read-only discovery block first to map the target machine's CPU topology, VBS state, GPU VBIOS power limits, Process Lasso installation, and installed games:

```powershell
$cpu = Get-CimInstance Win32_Processor
$cs = Get-CimInstance Win32_ComputerSystem
$vbs = (Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard -ErrorAction SilentlyContinue).VirtualizationBasedSecurityStatus
$ram = Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer, Speed, ConfiguredClockSpeed, Capacity

[PSCustomObject]@{
    CPU               = $cpu.Name.Trim()
    PhysicalCores     = $cpu.NumberOfCores
    LogicalThreads    = $cpu.NumberOfLogicalProcessors
    MaxClockMHz       = $cpu.MaxClockSpeed
    L3CacheKB         = $cpu.L3CacheSize
    TotalRAM_GB       = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    RAM_SpeedMHz      = ($ram | Select-Object -First 1).ConfiguredClockSpeed
    VBS_Status        = $vbs # 0 = Disabled (Optimal), 2 = Running (10-15% L3 cache penalty)
    ProcessLassoFound = (Test-Path "C:\ProgramData\ProcessLasso\config\prolasso.ini")
} | Format-List

nvidia-smi --query-gpu=name,driver_version,power.limit,power.default_limit,power.max_limit,temperature.gpu --format=csv 2>$null
```

---

## 3. Phase 2: VBS / Hypervisor & BIOS Baseline

### A. Windows VBS / Memory Integrity (HVCI)
- If `VBS_Status` is `2` (Running), nested page-table translations impose a **10%–18% penalty on 1% low FPS** in L3-cache-bound games (Deadlock, Valorant, CS2).
- **Riot Vanguard Compatibility:** On Windows 11, Riot Vanguard does **not** require VBS/Memory Integrity to be enabled as long as **TPM 2.0** and **Secure Boot** are enabled in BIOS.
- To disable VBS (requires Admin + Reboot, or toggle **Off** in *Windows Security $\rightarrow$ Device Security $\rightarrow$ Core Isolation $\rightarrow$ Memory Integrity*):
  ```powershell
  reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f
  reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f
  bcdedit /set hypervisorlaunchtype off
  ```

### B. BIOS Checklist (Present to User if Rebooting)
- **Memory Profile:** Enable **DOCP / XMP / EXPO** (verify `RAM_SpeedMHz` matches rated kit speed).
- **AMD Ryzen Infinity Fabric (Zen 3 / DDR4):** Lock `FCLK Frequency` to `RAM_SpeedMHz / 2` (e.g., `1800MHz` for `DDR4-3600`) to force 1:1 coupled mode.
- **PCIe Resizable BAR:** Enable `Above 4G Decoding` + `Re-Size BAR Support`.
- **AMD SMU / Scheduler:** Enable `CPPC`, `CPPC Preferred Cores`, and `Global C-States`.
- **Precision Boost Overdrive (PBO2):** Set `PBO = Advanced`, `PBO Limits = Motherboard`, `Curve Optimizer = All Cores, Negative, 15 to 20` (typically yields `+100 MHz` sustained all-core boost in teamfights while reducing temperatures).

---

## 4. Phase 3: Portable System-Wide Game & Hardware Tuner

Run this self-adapting PowerShell script to configure **DirectX Flip-Model (`HKCU`)**, **GameDVR disable (`HKCU`)**, **Process Lasso (`prolasso.ini`)**, **Windows Kernel `PerfOptions` (`HKLM`)**, **MMCSS Network Unthrottling (`HKLM`)**, and **NVIDIA GPU Power Limit Unlock**:

> **Agent Execution Note:** If the agent's terminal runs inside a sandboxed Job Object where `Start-Process -Verb RunAs` returns `The request is not supported`, save the script below to `$env:TEMP\eveoptimize_apply.ps1`, create a self-elevating `.bat` wrapper on the user's Desktop, open Explorer with `explorer.exe /select,"<path-to-bat>"` for the user to double-click, verify the changes, and delete the temporary `.bat`.

```powershell
$ErrorActionPreference = 'Continue'

# --- 1. Compute CPU Topology Masks Dynamically ---
$cpu = Get-CimInstance Win32_Processor
$totalThreads = [int]$cpu.NumberOfLogicalProcessors
$lastThread = $totalThreads - 1
$bgStartThread = [math]::Max(0, $totalThreads - 2)
$allCoresRange = "0-$lastThread"
$bgCoresRange = "$bgStartThread-$lastThread"
$bgAffinityMask = ([int64]1 -shl $bgStartThread) -bor ([int64]1 -shl $lastThread)

Write-Host "[EVEOPTIMIZE] Detected $totalThreads threads: Games -> $allCoresRange | Background Helpers -> $bgCoresRange (0x$('{0:X}' -f $bgAffinityMask))" -ForegroundColor Cyan

# --- 2. Auto-Discover Installed Game Executables Across Local Drives ---
$knownGamePatterns = @(
    "*\Deadlock\game\bin\win64\deadlock.exe",
    "*\VALORANT\live\ShooterGame\Binaries\Win64\VALORANT-Win64-Shipping.exe",
    "*\VALORANT\live\VALORANT.exe",
    "*\Overwatch\_retail_\Overwatch.exe",
    "*\Aniimo\Aniimo.exe",
    "*\Marvel*\Marvel-Win64-Shipping.exe",
    "*\League of Legends\Game\League of Legends.exe",
    "*\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"
)

$commonRoots = @(
    "C:\Program Files (x86)\Steam\steamapps\common",
    "C:\Program Files\Steam\steamapps\common",
    "D:\SteamLibrary\steamapps\common",
    "E:\SteamLibrary\steamapps\common",
    "C:\Riot Games",
    "D:\Riot Games",
    "C:\Program Files (x86)\Overwatch",
    "D:\Overwatch"
) | Where-Object { Test-Path $_ }

$foundGameExes = @()
foreach ($root in $commonRoots) {
    $exes = Get-ChildItem -Path $root -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue |
        Where-Object {
            $full = $_.FullName
            ($knownGamePatterns | Where-Object { $full -like $_ }).Count -gt 0
        }
    $foundGameExes += $exes.FullName
}
$foundGameExes = $foundGameExes | Select-Object -Unique

# --- 3. Apply DirectX High-Performance & Flip-Model Optimizations (HKCU) ---
$gpuPrefPath = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"
if (-not (Test-Path $gpuPrefPath)) { New-Item -Path $gpuPrefPath -Force | Out-Null }
foreach ($exePath in $foundGameExes) {
    Set-ItemProperty -Path $gpuPrefPath -Name $exePath -Value "GpuPreference=2;SwapEffectUpgradeEnable=1;" -Type String
    Write-Host "[OK] DirectX Flip-Model + High-Perf GPU bound: $exePath" -ForegroundColor Green
}

# --- 4. Disable Background GameDVR Ring Buffer & Force Exclusive Fullscreen (HKCU) ---
$dvrPath = "HKCU:\System\GameConfigStore"
Set-ItemProperty -Path $dvrPath -Name "GameDVR_Enabled" -Value 0 -Type DWord -ErrorAction SilentlyContinue
Set-ItemProperty -Path $dvrPath -Name "GameDVR_FSEBehaviorMode" -Value 2 -Type DWord -ErrorAction SilentlyContinue
Set-ItemProperty -Path $dvrPath -Name "GameDVR_HonorUserFSEBehaviorMode" -Value 1 -Type DWord -ErrorAction SilentlyContinue
Set-ItemProperty -Path $dvrPath -Name "GameDVR_DXGIHonorFSEWindowsCompatible" -Value 1 -Type DWord -ErrorAction SilentlyContinue
Set-ItemProperty -Path $dvrPath -Name "GameDVR_EFSEFeatureFlags" -Value 0 -Type DWord -ErrorAction SilentlyContinue

$appCapPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR"
if (-not (Test-Path $appCapPath)) { New-Item -Path $appCapPath -Force | Out-Null }
Set-ItemProperty -Path $appCapPath -Name "AppCaptureEnabled" -Value 0 -Type DWord -ErrorAction SilentlyContinue

# --- 5. Configure Process Lasso If Installed (Requires Admin, UTF-16LE) ---
$iniPath = "C:\ProgramData\ProcessLasso\config\prolasso.ini"
if (Test-Path $iniPath) {
    Copy-Item $iniPath "$iniPath.bak_eveoptimize" -Force
    $content = [System.IO.File]::ReadAllText($iniPath, [System.Text.Encoding]::Unicode)

    $priorities = "DefaultPriorities=valorant-win64-shipping.exe,high,valorant.exe,high,marvel-win64-shipping.exe,high,marvel.exe,high,overwatch.exe,high,aniimo.exe,high,league of legends.exe,high,cs2.exe,high,project_citadel.exe,high,deadlock.exe,high,discordsystemhelper.exe,normal,discord.exe,below normal,steamwebhelper.exe,below normal,epicwebhelper.exe,below normal,blizzardbrowser.exe,below normal,leagueclientuxrender.exe,below normal,icloudphotos.exe,idle,iclouddrive.exe,idle,apsdaemon.exe,idle"
    $ioPriorities = "DefaultIOPriorities=project_citadel.exe,3,deadlock.exe,3,valorant-win64-shipping.exe,3,overwatch.exe,3,aniimo.exe,3,marvel-win64-shipping.exe,3,league of legends.exe,3,cs2.exe,3"
    $memPriorities = "DefaultMemoryPriorities=project_citadel.exe,5,deadlock.exe,5,valorant-win64-shipping.exe,5,overwatch.exe,5,aniimo.exe,5,marvel-win64-shipping.exe,5,league of legends.exe,5,cs2.exe,5"
    $gpuPriorities = "DefaultGPUPriorities=overwatch.exe,4,deadlock.exe,4,valorant-win64-shipping.exe,4,aniimo.exe,4,marvel-win64-shipping.exe,4"
    $affinities = "DefaultAffinitiesEx=discord.exe,0,$bgCoresRange,steamwebhelper.exe,0,$bgCoresRange,epicwebhelper.exe,0,$bgCoresRange,blizzardbrowser.exe,0,$bgCoresRange,leagueclientuxrender.exe,0,$bgCoresRange,project_citadel.exe,0,$allCoresRange,deadlock.exe,0,$allCoresRange,valorant-win64-shipping.exe,0,$allCoresRange,valorant.exe,0,$allCoresRange,overwatch.exe,0,$allCoresRange,aniimo.exe,0,$allCoresRange,marvel-win64-shipping.exe,0,$allCoresRange,marvel.exe,0,$allCoresRange,league of legends.exe,0,$allCoresRange,cs2.exe,0,$allCoresRange"
    $gamingPaths = "AutomaticGamingModeProcessPaths=project_citadel.exe;deadlock.exe;valorant-win64-shipping.exe;overwatch.exe;aniimo.exe;marvel-win64-shipping.exe;league of legends.exe;cs2.exe;"

    $content = $content -replace 'DefaultPriorities=.*', $priorities
    $content = $content -replace 'DefaultIOPriorities=.*', $ioPriorities
    $content = $content -replace 'DefaultMemoryPriorities=.*', $memPriorities
    $content = $content -replace 'DefaultGPUPriorities=.*', $gpuPriorities
    $content = $content -replace 'DefaultAffinitiesEx=.*', $affinities
    $content = $content -replace 'AutomaticGamingModeProcessPaths=.*', $gamingPaths

    [System.IO.File]::WriteAllText($iniPath, $content, [System.Text.Encoding]::Unicode)
    Write-Host "[OK] Process Lasso updated ($allCoresRange for games, $bgCoresRange for background helpers)." -ForegroundColor Green
}

# --- 6. Live Quarantine of Running Background Helpers ---
Get-Process discord, steamwebhelper, epicwebhelper, blizzardbrowser, leagueclientuxrender -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $_.ProcessorAffinity = [IntPtr]$bgAffinityMask
        $_.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
    } catch {}
}

# --- 7. Windows Kernel PerfOptions & MMCSS Network Unthrottling (Requires Admin) ---
$ifeoBase = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
$gameExes = @("deadlock.exe", "VALORANT-Win64-Shipping.exe", "Overwatch.exe", "Aniimo.exe", "Marvel-Win64-Shipping.exe", "League of Legends.exe", "cs2.exe")
foreach ($exe in $gameExes) {
    $perfKey = Join-Path $ifeoBase "$exe\PerfOptions"
    if (-not (Test-Path $perfKey)) { New-Item -Path $perfKey -Force | Out-Null }
    Set-ItemProperty -Path $perfKey -Name "CpuPriorityClass" -Value 3 -Type DWord
    Set-ItemProperty -Path $perfKey -Name "IoPriority" -Value 3 -Type DWord
}

$mmcssSystem = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
if (Test-Path $mmcssSystem) {
    Set-ItemProperty -Path $mmcssSystem -Name "NetworkThrottlingIndex" -Value 0xFFFFFFFF -Type DWord
    Set-ItemProperty -Path $mmcssSystem -Name "SystemResponsiveness" -Value 10 -Type DWord
}
$mmcssGames = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
if (Test-Path $mmcssGames) {
    Set-ItemProperty -Path $mmcssGames -Name "GPU Priority" -Value 8 -Type DWord
    Set-ItemProperty -Path $mmcssGames -Name "Priority" -Value 6 -Type DWord
    Set-ItemProperty -Path $mmcssGames -Name "Scheduling Category" -Value "High" -Type String
    Set-ItemProperty -Path $mmcssGames -Name "SFIO Priority" -Value "High" -Type String
}

# --- 8. Dynamic NVIDIA Power Limit Unlock (94% of VBIOS Max if > Default) ---
$gpuLimits = nvidia-smi --query-gpu=power.default_limit,power.max_limit --format=csv,noheader,nounits 2>$null
if ($gpuLimits) {
    $parts = $gpuLimits.Split(',') | ForEach-Object { [double]$_.Trim() }
    $defW = $parts[0]
    $maxW = $parts[1]
    if ($maxW -gt ($defW + 15)) {
        $targetW = [math]::Floor([math]::Min($maxW, [math]::Round($maxW * 0.94 / 5) * 5))
        & nvidia-smi.exe -pl $targetW
        $action = New-ScheduledTaskAction -Execute "C:\Windows\System32\nvidia-smi.exe" -Argument "-pl $targetW"
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName "EVEOPTIMIZE_GPU_PowerLimit" -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
        Write-Host "[OK] NVIDIA Power Limit raised from $defW W to $targetW W (Max VBIOS: $maxW W)." -ForegroundColor Green
    }
}
```

---

## 5. Phase 4: Deadlock (Source 2) & Mod Manager Deep Tuning

### A. Deadlock Mod Manager (DMM) "Launch Without Mods" + Custom `gameinfo.gi` Fix
DMM validates `<Deadlock>\game\citadel\gameinfo.gi` against `gameinfo.gi.bak` by removing its `// Deadlock Mod Manager - Start ... End` block and comparing the files byte-for-byte.
1. Wrap the `SearchPaths` block in `gameinfo.gi` with:
   ```text
   		// Deadlock Mod Manager - Start
   		SearchPaths
   		{
   			Game				citadel
   			Game				core
   		}
   		// Deadlock Mod Manager - End
   ```
2. Save an identical copy to `gameinfo.gi.bak` **without** the `// Deadlock Mod Manager - Start` and `// Deadlock Mod Manager - End` lines.
3. Always write both files with **UTF-8 No-BOM** (`New-Object System.Text.UTF8Encoding($false)`).

### B. The 4 High-Impact Teamfight ConVars in `gameinfo.gi`
Ensure these overrides are set inside `gameinfo.gi` (and mirrored in `gameinfo.gi.bak`):
- `lb_enable_dynamic_lights "false"` — Disables dynamic ability/projectile light bounces on map geometry (saves 15%–25% GPU and render-thread time in 6v6 fights).
- `citadel_portrait_world_renderer_off "true"` — Disables live 3D hero portrait world rendering in the HUD.
- `r_citadel_enable_pano_world_blur "false"` — Disables Panorama UI world blur pass.
- `cl_updaterate "64"` — Matches Deadlock's native 64-tick server rate (do not leave at `128`).
- `csm_max_num_cascades_override "0"` and `sc_screen_size_lod_scale_override "0.55"`.

### C. Launch Options & Renderer Backend
- **Steam Launch Options:** `-console -threads <PhysicalCores + 1> -nojoy -nosteamcontroller -nohltv +exec autoexec.cfg`
- **Renderer (`<Deadlock>\game\citadel\cfg\boot.vcfg`):** Set `"prefer_vulkan" "-dx11"` on NVIDIA Turing/Ampere GPUs to avoid 35–40ms Vulkan shader pipeline hitches.

---

## 6. Phase 5: Discreet Live Match Telemetry Profiler

To diagnose whether a user is CPU L3-cache bound, GPU bound, thermally throttling, or suffering from background process spikes during an actual match, launch this low-overhead logger in the background (samples every 5 seconds to `$env:TEMP\eveoptimize_telemetry.csv`):

```powershell
param(
    [string]$ProcessName = "deadlock",
    [string]$OutCsv = "$env:TEMP\eveoptimize_telemetry.csv",
    [int]$IntervalSec = 5,
    [int]$MaxDurationSec = 1800
)

"Timestamp,ElapsedSec,GameCpuPct,TotalCpuPct,CpuBoostMHz,GameRamMB,FreeSysRamMB,GpuUtilPct,GpuMemUtilPct,GpuTempC,GpuClockMHz,GpuPowerW,GpuFanPct" | Set-Content -Path $OutCsv -Encoding UTF8

$start = Get-Date
$logicalCores = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$baseClock = (Get-CimInstance Win32_Processor).MaxClockSpeed
$dlProc1 = Get-Process $ProcessName -ErrorAction SilentlyContinue
$t1 = Get-Date
$cpuTime1 = if ($dlProc1) { $dlProc1.TotalProcessorTime.TotalSeconds } else { 0 }

while (((Get-Date) - $start).TotalSeconds -lt $MaxDurationSec) {
    $counters = Get-Counter '\Processor Information(_Total)\% Processor Performance', '\Processor(_Total)\% Processor Time', '\Memory\Available MBytes' -SampleInterval 2 -MaxSamples 1 -ErrorAction SilentlyContinue
    $dlProc2 = Get-Process $ProcessName -ErrorAction SilentlyContinue
    $t2 = Get-Date
    $dt = ($t2 - $t1).TotalSeconds

    if ($dlProc2 -and $dt -gt 0) {
        $cpuTime2 = $dlProc2.TotalProcessorTime.TotalSeconds
        $dlCpuPct = [math]::Round((($cpuTime2 - $cpuTime1) / ($dt * $logicalCores)) * 100, 1)
        if ($dlCpuPct -lt 0) { $dlCpuPct = 0 }
        $dlRamMB = [math]::Round($dlProc2.WorkingSet64 / 1MB, 0)
        $cpuTime1 = $cpuTime2
    } else {
        $dlCpuPct = 0; $dlRamMB = 0
    }
    $t1 = $t2

    $perfPct = ($counters.CounterSamples | Where-Object { $_.Path -like '*Processor Performance*' }).CookedValue
    $totalCpuPct = [math]::Round(($counters.CounterSamples | Where-Object { $_.Path -like '*% Processor Time*' }).CookedValue, 1)
    $freeRamMB = [math]::Round(($counters.CounterSamples | Where-Object { $_.Path -like '*Available MBytes*' }).CookedValue, 0)
    $boostMHz = [math]::Round($baseClock * ($perfPct / 100.0), 0)

    $gpuRaw = nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,clocks.current.graphics,power.draw,fan.speed --format=csv,noheader,nounits 2>$null
    $gpuLine = if ($gpuRaw) { ($gpuRaw.Split(',') | ForEach-Object { $_.Trim() }) -join ',' } else { "0,0,0,0,0,0" }

    $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    "$((Get-Date).ToString('HH:mm:ss')),$elapsed,$dlCpuPct,$totalCpuPct,$boostMHz,$dlRamMB,$freeRamMB,$gpuLine" | Add-Content -Path $OutCsv -Encoding UTF8
    Start-Sleep -Seconds $IntervalSec
}
```

### How to Interpret Telemetry Results
- **`GpuUtilPct` `90%–99%`:** System is cleanly GPU-bound (delivering maximum frames the GPU can render).
- **`GpuUtilPct` drops to `55%–75%` while `GameCpuPct` plateaus at `35%–45%`:** The game's Main/Render threads and worker pool are saturated and hitting the CPU's **L3 Cache capacity/latency ceiling** during heavy ability/entity spam.
- **`TotalCpuPct - GameCpuPct > 15%` mid-fight:** Background processes escaped core isolation and caused OS context-switching stutters.
- **`GpuTempC >= 84°C` with dropping `GpuClockMHz`:** GPU hit NVIDIA's stock thermal throttle target; raise Temp Limit to `88°C` or increase fan curve in MSI Afterburner / NVIDIA App.

---

## 7. Phase 6: "The Last Drop" — PCIe Interrupt Offload, Kernel Memory & Ghost Daemon Audit

Once Phases 1–5 are verified, apply this final kernel/hardware pass to tighten `0.1%` / `1%` frame-time lows and eliminate micro-stutters caused by Core 0 ISR/DPC contention, kernel memory compression, delayed TCP ACKs, or invisible background scans:

### A. Why Core 0 Interrupt Offloading Matters
By default on Windows, even when PCIe MSI Mode (`MSISupported = 1`) is active, `DevicePolicy` is unset—routing **100% of GPU (`nvlddmkm.sys` / `dxgkrnl.sys`) and Network (`ndis.sys`) hardware interrupts onto Logical Core 0**, which is the exact core where Source 2 and Unreal Engine schedule the game's **Main Thread**.
- **Fix:** Pin the GPU's MSI interrupts to **Logical Core 2 (Physical Core 1, mask `04 00`)** at `High` priority (`DevicePriority = 3`), and pin Network Adapter interrupts to **Logical Core 4 (Physical Core 2, mask `10 00`)** at `Normal` priority (`DevicePriority = 2`).

### B. Portable "Last Drop" Kernel & Interrupt Script (Requires Admin)

```powershell
$ErrorActionPreference = 'Continue'

# --- 1. Offload GPU & Network PCIe MSI Interrupts Off Core 0 ---
Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Display' -and $_.InstanceId -like 'PCI*' } | ForEach-Object {
    $msiKey = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.InstanceId)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    $affKey = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.InstanceId)\Device Parameters\Interrupt Management\Affinity Policy"
    if (-not (Test-Path $msiKey)) { New-Item -Path $msiKey -Force | Out-Null }
    if (-not (Test-Path $affKey)) { New-Item -Path $affKey -Force | Out-Null }
    Set-ItemProperty -Path $msiKey -Name "MSISupported" -Value 1 -Type DWord
    Set-ItemProperty -Path $affKey -Name "DevicePriority" -Value 3 -Type DWord
    Set-ItemProperty -Path $affKey -Name "DevicePolicy" -Value 4 -Type DWord
    Set-ItemProperty -Path $affKey -Name "AssignmentSetOverride" -Value ([byte[]](0x04, 0x00)) -Type Binary
    Write-Host "[OK] GPU MSI Interrupts ($($_.FriendlyName)): Priority=High(3), Pinned to Core 2 (Offloaded from Core 0)." -ForegroundColor Green
}

Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Net' -and $_.InstanceId -like 'PCI*' } | ForEach-Object {
    $msiKey = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.InstanceId)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    $affKey = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.InstanceId)\Device Parameters\Interrupt Management\Affinity Policy"
    if (-not (Test-Path $msiKey)) { New-Item -Path $msiKey -Force | Out-Null }
    if (-not (Test-Path $affKey)) { New-Item -Path $affKey -Force | Out-Null }
    Set-ItemProperty -Path $msiKey -Name "MSISupported" -Value 1 -Type DWord
    Set-ItemProperty -Path $affKey -Name "DevicePriority" -Value 2 -Type DWord
    Set-ItemProperty -Path $affKey -Name "DevicePolicy" -Value 4 -Type DWord
    Set-ItemProperty -Path $affKey -Name "AssignmentSetOverride" -Value ([byte[]](0x10, 0x00)) -Type Binary
    Write-Host "[OK] NIC MSI Interrupts ($($_.FriendlyName)): Priority=Normal(2), Pinned to Core 4 (Offloaded from Core 0)." -ForegroundColor Green
}

# --- 2. Kernel Foreground Quantum & Executive Paging ---
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl" -Name "Win32PrioritySeparation" -Value 38 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name "DisablePagingExecutive" -Value 1 -Type DWord

# --- 3. Disable Windows Kernel Memory Compression (Saves L3 Cache Bandwidth) ---
Disable-MMAgent -MemoryCompression -ErrorAction SilentlyContinue
Write-Host "[OK] Windows Kernel Memory Compression disabled." -ForegroundColor Green

# --- 4. Disable Nagle's Algorithm (TcpAckFrequency=1, TCPNoDelay=1) on Active NICs ---
Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" | ForEach-Object {
    $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
    if ($p.DhcpIPAddress -or $p.IPAddress) {
        Set-ItemProperty -Path $_.PSPath -Name "TcpAckFrequency" -Value 1 -Type DWord
        Set-ItemProperty -Path $_.PSPath -Name "TCPNoDelay" -Value 1 -Type DWord
        Write-Host "[OK] Disabled Nagle's Algorithm on interface $($_.PSChildName)." -ForegroundColor Green
    }
}

# --- 5. Disable Legacy EmptyStandbyList Scheduled Tasks (Causes 10-Min Kernel PFN Stutters & Purges Shader Cache) ---
Get-ScheduledTask | Where-Object { $_.TaskName -match "EMPTYSTANDBY|StandbyList" -or ($_.Actions.Execute -match "EmptyStandbyList") } | ForEach-Object {
    Disable-ScheduledTask -InputObject $_ -ErrorAction SilentlyContinue | Out-Null
    Write-Host "[OK] Disabled legacy standby-purge scheduled task: $($_.TaskName)" -ForegroundColor Green
}
```

### C. Ghost Daemon, Headless Defender Scan & `EmptyStandbyList` Audit
If `TotalCpuPct` still shows unexplained `6%–35%` background usage at idle or periodic mid-match hitches, check for these three silent culprits:
1. **Legacy `EmptyStandbyList.exe` Scheduled Tasks (Firing Every 5–10 Minutes):**
   - Many gaming PCs have a legacy 2017 Windows 10 scheduled task (`EMPTYSTANDBY`) running `EmptyStandbyList.exe` every 5–10 minutes (`PT5M` / `PT10M`).
   - On Windows 11, calling `MemoryPurgeStandbyList` mid-match locks the kernel Page Frame Number (PFN) database (causing an immediate 15–50ms stutter) and purges cached game `.vpk`/`.pak` assets and compiled GPU shader caches (`NV_Cache`) out of spare RAM, forcing hard page faults to disk. Always disable periodic `EmptyStandbyList` tasks (Process Lasso's `ClearStandbyFreeRAMThresholdMB=1024` handles low-RAM edge cases safely without blind timers).
2. **Crash-Looping Local Agent Supervisors (`node.exe` / `python.exe`):**
   - Inspect all running Node/Python processes and their accumulated CPU seconds:
     ```powershell
     Get-CimInstance Win32_Process -Filter "Name = 'node.exe' OR Name = 'python.exe'" | Select-Object ProcessId, CommandLine
     ```
   - Watch for local bridges/gateways (e.g., `supervisor.mjs`, `openclaw`, local MCP daemons) crash-looping every 3 seconds against a closed localhost port—each `CreateProcess` + V8 JIT initialization spikes all CPU cores. Stop/disable unneeded background agents on gaming rigs.
3. **Headless WMI Windows Defender Scans (`Event ID 1000` without `1001`/`1002`):**
   - WMI-triggered scans (`Start-MpScan`) run invisibly inside `MsMpEng.exe` for up to 2 hours without showing a progress bar or Cancel button in the Windows Security GUI.
   - Check the Defender Operational Event Log and abort any active headless scan + force low CPU priority for future scans (requires Admin):
     ```powershell
     Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Windows Defender/Operational'; Id=1000,1001,1002} -MaxEvents 3 | Select-Object TimeCreated, Id, Message | Format-List
     $mp = Get-ChildItem "C:\ProgramData\Microsoft\Windows Defender\Platform\*\MpCmdRun.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
     if ($mp) { & $mp.FullName -Scan -Cancel }
     Set-MpPreference -EnableLowCpuPriority $true -ScanAvgCPULoadFactor 5 -ErrorAction SilentlyContinue
     ```


