---
name: eveoptimize
description: >-
  EVEOPTIMIZE: Portable, agent-executable competitive PC gaming optimization tuner.
  Dynamically scans installed games across all drives, asks the user which title(s)
  to prioritize, identifies each game's engine (Source 2, Unreal Engine 4/5, Unity,
  or Custom), and applies tailored engine + OS + Process Lasso + BIOS/GPU/Kernel
  optimizations with live match telemetry profiling.
---

# Skill: EVEOPTIMIZE — Adaptive PC & Game-Engine Optimization Tuner

See [[02-Agents/Agent Registry]], [[02-Agents/Skills/experiment-design]], [[02-Agents/Skills/context-handoff]].

> [!IMPORTANT]
> **AGENT BOOTSTRAP (READ THIS FIRST):** Built-in web-fetch tools (`read_url_content` / `webfetch`) truncate responses at **8 KB (~line 115)**. You **MUST** first download this complete runbook to disk via PowerShell and read it locally with `view_file`:
> ```powershell
> Invoke-RestMethod "https://raw.githubusercontent.com/existinge/EVEATLAS/main/02-Agents/Skills/EVEOPTIMIZE.md" -OutFile "$env:TEMP\EVEOPTIMIZE.md"
> ```
> Once downloaded, call `view_file` on `$env:TEMP\EVEOPTIMIZE.md` (`StartLine=1, EndLine=500`) to read all phases completely before executing!

**Purpose:** Enable any autonomous coding agent (Antigravity, Claude Code, Cursor, OpenClaw) to perform a deterministic, hardware-aware and **game-engine-specific** optimization and live telemetry audit on any Windows gaming PC—**without hardcoded game lists, hardcoded user paths, or blind placebo tweaks**.

---

## 1. Core Engineering Rules (Non-Negotiable)

1. **Never Hardcode Game Titles—Always Scan & Ask First:**
   - Every user plays different titles across different engines. The agent must **scan all local drives for installed games**, classify each game's engine (**Source 2**, **Unreal Engine 4/5**, **Unity**, or **Custom Engine**), and **ask the user which game(s) they want to prioritize**.
2. **Never Starve Games of Physical Cores in Process Lasso:**
   - Never restrict a modern game to a subset of cores on a single-CCD CPU (e.g., locking an 8-core/16-thread CPU to `0–11` / `0xFFF`). Doing so cuts off physical cores and forces game worker threads onto SMT sibling hyperthreads where they contend with the Main and Render threads.
   - **Correct Rule:** Dynamically query total logical threads $T$ (`0` to $T-1$). Grant all discovered/selected games **all threads (`0..(T-1)`)** at `High` priority, and quarantine detected background Chromium/overlay helpers (`discord.exe`, `steamwebhelper.exe`, `epicwebhelper.exe`, `blizzardbrowser.exe`, `leagueclientuxrender.exe`, `overwolfbrowser.exe`) to the **last physical core (`(T-2)-(T-1)`)** at **`Below Normal`** priority.
3. **Always Target the Real Shipping Binary (Not the Launcher Stub):**
   - Many games (especially Unreal Engine 4/5) have a root launcher `.exe` that spawns a child `*-Win64-Shipping.exe` binary under `Binaries\Win64\`.
   - Always resolve and target the actual runtime binary (e.g., `*-Win64-Shipping.exe` for Unreal, `game\bin\win64\*.exe` for Source 2) in Process Lasso, Windows Kernel `PerfOptions`, and DirectX `UserGpuPreferences`.

---

## 2. Phase 1: Dynamic Hardware, OS & Game-Engine Discovery (Run First)

Execute this read-only discovery script first. It maps the user's CPU topology, VBS state, GPU VBIOS power limits, connected monitors, and **automatically scans all drives to discover installed games and classify their game engine**:

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

# --- Auto-Scan Installed Games & Identify Engine Type Across All Drives ---
$drives = Get-PSDrive -PSProvider FileSystem | Select-Object -ExpandProperty Root
$libraryRoots = @()
foreach ($d in $drives) {
    foreach ($sub in @(
        "Program Files (x86)\Steam\steamapps\common",
        "Program Files\Steam\steamapps\common",
        "SteamLibrary\steamapps\common",
        "Program Files\Epic Games",
        "Epic Games",
        "Riot Games",
        "Program Files (x86)\Overwatch",
        "Overwatch",
        "XboxGames",
        "GOG Games"
    )) {
        $p = Join-Path $d $sub
        if (Test-Path $p) { $libraryRoots += $p }
    }
}

$discoveredGames = foreach ($lib in ($libraryRoots | Select-Object -Unique)) {
    Get-ChildItem -Path $lib -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $gameDir = $_.FullName
        $exes = Get-ChildItem -Path $gameDir -Recurse -Depth 4 -Filter "*.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "Crash|Unins|Setup|Clean|Repair|DXSETUP|vc_redist|UnityCrash|Helper|Launcher|Updater|Benchmark|Server" }

        if ($exes) {
            $engine = "Custom / Native"
            $primaryExe = $exes | Sort-Object Length -Descending | Select-Object -First 1

            $ueShipping = $exes | Where-Object { $_.Name -like "*-Win64-Shipping.exe" -or $_.FullName -like "*\Binaries\Win64\*.exe" } | Sort-Object Length -Descending | Select-Object -First 1
            $source2Exe = $exes | Where-Object { $_.FullName -like "*\game\bin\win64\*.exe" } | Select-Object -First 1
            $hasGameInfo = Test-Path (Join-Path $gameDir "game\*\gameinfo.gi")
            $hasUnity = (Test-Path (Join-Path $gameDir "UnityPlayer.dll")) -or ((Get-ChildItem $gameDir -Directory -Filter "*_Data" -ErrorAction SilentlyContinue).Count -gt 0)

            if ($source2Exe -or $hasGameInfo) {
                $engine = "Source 2"
                if ($source2Exe) { $primaryExe = $source2Exe }
            } elseif ($ueShipping) {
                $engine = "Unreal Engine (UE4/UE5)"
                $primaryExe = $ueShipping
            } elseif ($hasUnity) {
                $engine = "Unity"
            }

            [PSCustomObject]@{
                GameTitle  = $_.Name
                Engine     = $engine
                ExeName    = $primaryExe.Name
                ExePath    = $primaryExe.FullName
                InstallDir = $gameDir
            }
        }
    }
}
$discoveredGames | Format-Table -AutoSize
```

### Mandatory User Check-In After Phase 1
Present the discovered hardware summary and the table of detected games + engines to the user, and **ask**:
1. **Which primary game(s)** they want deep engine-level optimization for (e.g., a Source 2 title, an Unreal Engine 4/5 shooter, a Unity title, etc.).
2. Whether they want **all discovered games** included in the system-wide Process Lasso / DirectX / Kernel priority rules (recommended).

---

## 3. Phase 2: VBS / Hypervisor & BIOS Baseline

### A. Windows VBS / Memory Integrity (HVCI)
- If `VBS_Status` is `2` (Running), nested page-table translations impose a **10%–18% penalty on 1% low FPS** in L3-cache-bound games (Source 2, Unreal Engine 5, competitive shooters).
- **Anti-Cheat Note (Riot Vanguard / BattleEye / EAC):** On Windows 11, kernel anti-cheats work cleanly with VBS/Memory Integrity **Off (`0`)** as long as **TPM 2.0** and **Secure Boot** remain enabled in BIOS.
- To disable VBS (requires Admin + Reboot, or toggle **Off** in *Windows Security $\rightarrow$ Device Security $\rightarrow$ Core Isolation $\rightarrow$ Memory Integrity*):
  ```powershell
  reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f
  reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f
  bcdedit /set hypervisorlaunchtype off
  ```

### B. BIOS Checklist (Present to User if Rebooting)
- **Memory Profile:** Enable **DOCP / XMP / EXPO** (verify `RAM_SpeedMHz` matches rated kit speed).
- **AMD Ryzen Infinity Fabric (Zen 3 / DDR4):** Lock `FCLK Frequency` to `RAM_SpeedMHz / 2` (e.g., `1800MHz` for `DDR4-3600`) to force 1:1 coupled mode.
- **PCIe Resizable BAR:** Enable `Above 4G Decoding` + `Re-Size BAR Support` (or `Smart Access Memory`).
- **AMD SMU / Scheduler:** Enable `CPPC`, `CPPC Preferred Cores`, and `Global C-States`.
- **Precision Boost Overdrive (PBO2):** Set `PBO = Advanced`, `PBO Limits = Motherboard`, `Curve Optimizer = All Cores, Negative, 15 to 20` (raises sustained all-core gaming boost by `+75–125 MHz` while lowering temps).

---

## 4. Phase 3: Dynamic System-Wide Scheduler, DirectX & GPU Power Tuner

This script **dynamically binds whatever games were discovered/confirmed in Phase 1** (zero hardcoded game lists) into **DirectX Flip-Model (`HKCU`)**, **Process Lasso (`prolasso.ini`)**, **Windows Kernel `PerfOptions` (`HKLM`)**, **MMCSS Network Unthrottling (`HKLM`)**, and **NVIDIA GPU Power Limit Unlock**:

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

# --- 2. Use Discovered Game Executables ($discoveredGames from Phase 1) ---
# Ensure $targetGameExes contains the full paths of all discovered/selected game binaries:
$targetGamePaths = $discoveredGames.ExePath | Select-Object -Unique
$targetGameNames = ($discoveredGames.ExeName | ForEach-Object { $_.ToLower() }) | Select-Object -Unique

# --- 3. Apply DirectX High-Performance & Flip-Model Optimizations (HKCU) ---
$gpuPrefPath = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"
if (-not (Test-Path $gpuPrefPath)) { New-Item -Path $gpuPrefPath -Force | Out-Null }
foreach ($exePath in $targetGamePaths) {
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

# --- 5. Dynamically Configure Process Lasso If Installed (Requires Admin, UTF-16LE) ---
$iniPath = "C:\ProgramData\ProcessLasso\config\prolasso.ini"
$bgHelpers = @("discord.exe", "steamwebhelper.exe", "epicwebhelper.exe", "blizzardbrowser.exe", "leagueclientuxrender.exe", "overwolfbrowser.exe")

if (Test-Path $iniPath) {
    Copy-Item $iniPath "$iniPath.bak_eveoptimize" -Force
    $content = [System.IO.File]::ReadAllText($iniPath, [System.Text.Encoding]::Unicode)

    $prioEntries = ($targetGameNames | ForEach-Object { "$_,high" }) + ($bgHelpers | ForEach-Object { "$_,below normal" }) + @("icloudphotos.exe,idle", "iclouddrive.exe,idle", "apsdaemon.exe,idle")
    $ioEntries   = $targetGameNames | ForEach-Object { "$_,3" }
    $memEntries  = $targetGameNames | ForEach-Object { "$_,5" }
    $gpuEntries  = $targetGameNames | ForEach-Object { "$_,4" }
    $affEntries  = ($bgHelpers | ForEach-Object { "$_,0,$bgCoresRange" }) + ($targetGameNames | ForEach-Object { "$_,0,$allCoresRange" })
    $gameModeStr = ($targetGameNames -join ";") + ";"

    $content = $content -replace 'DefaultPriorities=.*', ("DefaultPriorities=" + ($prioEntries -join ","))
    $content = $content -replace 'DefaultIOPriorities=.*', ("DefaultIOPriorities=" + ($ioEntries -join ","))
    $content = $content -replace 'DefaultMemoryPriorities=.*', ("DefaultMemoryPriorities=" + ($memEntries -join ","))
    $content = $content -replace 'DefaultGPUPriorities=.*', ("DefaultGPUPriorities=" + ($gpuEntries -join ","))
    $content = $content -replace 'DefaultAffinitiesEx=.*', ("DefaultAffinitiesEx=" + ($affEntries -join ","))
    $content = $content -replace 'AutomaticGamingModeProcessPaths=.*', ("AutomaticGamingModeProcessPaths=" + $gameModeStr)

    [System.IO.File]::WriteAllText($iniPath, $content, [System.Text.Encoding]::Unicode)
    Write-Host "[OK] Process Lasso dynamically updated for $($targetGameNames.Count) games ($allCoresRange) & background helpers ($bgCoresRange)." -ForegroundColor Green
}

# --- 6. Live Quarantine of Running Background Helpers ---
Get-Process discord, steamwebhelper, epicwebhelper, blizzardbrowser, leagueclientuxrender, overwolfbrowser -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $_.ProcessorAffinity = [IntPtr]$bgAffinityMask
        $_.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
    } catch {}
}

# --- 7. Windows Kernel PerfOptions & MMCSS Network Unthrottling (Requires Admin) ---
$ifeoBase = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
foreach ($exe in $discoveredGames.ExeName) {
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

## 5. Phase 4: Engine-Specific Deep Tuning Modules (Apply Based on Target Game's Engine)

Select and apply the module(s) matching the engine of the game(s) the user prioritized in Phase 1:

### Module 4A: Unreal Engine 4 & 5 Titles (e.g., Valorant, Marvel Rivals, Fortnite, The Finals, Aniimo, etc.)
1. **Locate Config Directory:**
   - Check `$env:LOCALAPPDATA\<GameFolder>\Saved\Config\WindowsClient` (or `WindowsNoEditor` / `Windows`).
2. **`GameUserSettings.ini` Competitive Baseline:**
   - Ensure Fullscreen Exclusive mode (`FullscreenMode=0`, `LastConfirmedFullscreenMode=0`, `bUseDynamicResolution=False`, `bUseVSync=False`).
   - Disable heavy post-processing where exposed (`sg.PostProcessQuality=0`, `sg.ShadowQuality=0` or `1`, `sg.EffectsQuality=0`, `sg.FoliageQuality=0`, `sg.ShadingQuality=0`).
   - On UE5 titles with Lumen/Nanite (e.g., Marvel Rivals, Fortnite), disable Lumen Global Illumination / Reflections in favor of Screen Space or Off, and enable **DLSS / XeSS / TSR Quality (`75%–85%` 3D resolution)** if GPU-bound at 1440p/4K.
3. **NVIDIA Reflex & One-Frame Thread Lag:**
   - Enable **NVIDIA Reflex (`On + Boost`)** in-game so the UE render thread does not queue an extra frame ahead of the game thread.
   - Verify the `*-Win64-Shipping.exe` child binary (not the root launcher `.exe`) is registered in Process Lasso and `HKCU:\Software\Microsoft\DirectX\UserGpuPreferences`.

### Module 4B: Source 2 Engine Titles (e.g., Deadlock, Counter-Strike 2, Dota 2)
1. **Launch Options & Worker Thread Allocation:**
   - Set Steam Launch Options to: `-console -threads <PhysicalCores + 1> -nojoy -nosteamcontroller -nohltv +exec autoexec.cfg`
   - **Never use `-no_prewarm_map`**—skipping map asset prewarming forces synchronous shader/particle compilation on the first ability cast or grenade throw (~100 FPS hitch).
2. **Renderer Backend (`boot.vcfg`):**
   - On NVIDIA Turing/Ampere GPUs experiencing Vulkan shader pipeline stalls, set `"prefer_vulkan" "-dx11"` in `<GameDir>\game\*\cfg\boot.vcfg`.
3. **Custom `gameinfo.gi` & Mod Manager Compatibility (Deadlock):**
   - Never save `gameinfo.gi` with a UTF-8 BOM (`EF BB BF`)—always write using `New-Object System.Text.UTF8Encoding($false)`.
   - If Deadlock Mod Manager (DMM) is installed, wrap `SearchPaths` in `// Deadlock Mod Manager - Start ... End` in `gameinfo.gi` and keep `gameinfo.gi.bak` identical *without* those 2 marker lines so DMM's "Launch without mods" validation succeeds.
   - High-impact teamfight `gameinfo.gi` ConVars:
     - `lb_enable_dynamic_lights "false"` (saves 15%–25% GPU & render-thread time in 6v6 fights)
     - `citadel_portrait_world_renderer_off "true"`
     - `r_citadel_enable_pano_world_blur "false"`
     - `cl_updaterate "64"` (match native 64-tick server rate)
     - `csm_max_num_cascades_override "0"` & `sc_screen_size_lod_scale_override "0.55"`

### Module 4C: Unity Engine Titles (e.g., Escape from Tarkov, Rust, Unity Action/RPGs)
1. **Check `<GameDir>\*_Data\boot.config`:**
   - Ensure native multithreaded rendering jobs are enabled (`gfx-enable-gfx-jobs=1`, `gfx-enable-native-gfx-jobs=1`, `wait-for-native-debugger=0`, `gc-max-time-slice=3`). (Back up `boot.config` before editing; skip if the game uses strict file-integrity checks on `boot.config`.)
2. **Fullscreen Exclusive Override:**
   - Unity games default to borderless fullscreen (`-window-mode exclusive` in launch options or `SwapEffectUpgradeEnable=1` in `UserGpuPreferences` ensures hardware flip presentation).

### Module 4D: Custom Competitive Engines (e.g., Overwatch 2, League of Legends, Apex Legends)
1. **Overwatch 2 (`Documents\Overwatch\Settings\Settings_v0.ini`):**
   - Ensure `FullScreenRefresh` matches maximum monitor refresh rate, `ReduceBuffering = "1"`, `ReflexMode = "2"` (Enabled + Boost), `DynamicRenderScale = "0"`, `HighQualityUpsampling = "0"` (or AMD FSR 2.2 / DLSS if GPU-bound), and `LocalFogDetail = "1"` (Low).
2. **League of Legends (`Game\Config\game.cfg`):**
   - Enable `[General] PreferDX9LegacyMode=0`, `WaitForVerticalSync=0`, `EnableFXAA=0`, and quarantine `leagueclientuxrender.exe` (the Chromium client renderer) to the last CPU core (`(T-2)-(T-1)`) at `Below Normal` priority.

---

## 6. Phase 5: Discreet Live Match Telemetry Profiler (Works on Any Game)

Pass the user's target game process name (`-ProcessName "<exe_without_extension>"`) to capture 5-second interval telemetry during a live match without impacting FPS:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$ProcessName, # e.g. "VALORANT-Win64-Shipping", "Overwatch", "deadlock", "cs2"
    [string]$OutCsv = "$env:TEMP\eveoptimize_telemetry.csv",
    [int]$IntervalSec = 5,
    [int]$MaxDurationSec = 1800
)

"Timestamp,ElapsedSec,GameCpuPct,TotalCpuPct,CpuBoostMHz,GameRamMB,FreeSysRamMB,GpuUtilPct,GpuMemUtilPct,GpuTempC,GpuClockMHz,GpuPowerW,GpuFanPct" | Set-Content -Path $OutCsv -Encoding UTF8

$start = Get-Date
$logicalCores = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$baseClock = (Get-CimInstance Win32_Processor).MaxClockSpeed
$dlProc1 = Get-Process $ProcessName -ErrorAction SilentlyContinue | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
$t1 = Get-Date
$cpuTime1 = if ($dlProc1) { $dlProc1.TotalProcessorTime.TotalSeconds } else { 0 }

while (((Get-Date) - $start).TotalSeconds -lt $MaxDurationSec) {
    $counters = Get-Counter '\Processor Information(_Total)\% Processor Performance', '\Processor(_Total)\% Processor Time', '\Memory\Available MBytes' -SampleInterval 2 -MaxSamples 1 -ErrorAction SilentlyContinue
    $dlProc2 = Get-Process $ProcessName -ErrorAction SilentlyContinue | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
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

# --- 4. Disable Nagle's Algorithm (TcpAckFrequency=1, TCPNoDelay=1) on Active NICs ---
Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" | ForEach-Object {
    $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
    if ($p.DhcpIPAddress -or $p.IPAddress) {
        Set-ItemProperty -Path $_.PSPath -Name "TcpAckFrequency" -Value 1 -Type DWord
        Set-ItemProperty -Path $_.PSPath -Name "TCPNoDelay" -Value 1 -Type DWord
    }
}

# --- 5. Disable Legacy EmptyStandbyList Scheduled Tasks (Causes 10-Min Kernel PFN Stutters & Purges Shader Cache) ---
Get-ScheduledTask | Where-Object { $_.TaskName -match "EMPTYSTANDBY|StandbyList" -or ($_.Actions.Execute -match "EmptyStandbyList") } | ForEach-Object {
    Disable-ScheduledTask -InputObject $_ -ErrorAction SilentlyContinue | Out-Null
    Write-Host "[OK] Disabled legacy standby-purge scheduled task: $($_.TaskName)" -ForegroundColor Green
}
```

### Ghost Daemon, Headless Defender Scan & `EmptyStandbyList` Audit
1. **Legacy `EmptyStandbyList.exe` Scheduled Tasks (Firing Every 5–10 Minutes):**
   - Calling `MemoryPurgeStandbyList` on a 5/10-minute timer locks the kernel PFN database (15–50ms stutter) and purges cached game assets and compiled GPU shaders (`NV_Cache`) out of spare RAM. Always disable periodic `EmptyStandbyList` tasks (Process Lasso's `ClearStandbyFreeRAMThresholdMB=1024` handles low-RAM edge cases safely).
2. **Crash-Looping Local Agent Supervisors (`node.exe` / `python.exe`):**
   - Inspect running Node/Python processes (`Get-CimInstance Win32_Process -Filter "Name = 'node.exe' OR Name = 'python.exe'" | Select-Object ProcessId, CommandLine`) for local bridges/daemons crash-looping against closed ports every few seconds.
3. **Headless WMI Windows Defender Scans (`Event ID 1000` without `1001`/`1002`):**
   - Check `Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Windows Defender/Operational'; Id=1000,1001,1002} -MaxEvents 3`. Abort active headless scans via `MpCmdRun.exe -Scan -Cancel` and set `Set-MpPreference -EnableLowCpuPriority $true -ScanAvgCPULoadFactor 5`.

---

## 8. Phase 7: Multi-Monitor & High-Refresh DWM Optimization

1. **Phantom "Powered-Off" Monitors Still Rendering in Windows:**
   - Turning off a 2nd or 3rd monitor via its physical power button often only kills the backlight without dropping DisplayPort/HDMI Hot-Plug Detect (HPD). Windows (`dwm.exe`) and the GPU continue allocating VRAM and scanning out to the powered-off display (forcing NVIDIA GPUs into the `P0` max memory-clock state at 50–65W idle and mixing mismatched refresh rates).
   - **Rule:** Query `EnumDisplayDevices` + `EnumDisplaySettings` for all active desktop displays (`StateFlags & 1`). Ask the user which monitors they keep on while gaming, and disconnect any unused display in software (`dmPelsWidth = 0, dmPelsHeight = 0`) during gaming.
2. **Never Lower a Secondary Monitor's Resolution to Save FPS—Lower Its Refresh Rate Instead:**
   - Dropping a secondary `3440x1440` or `2560x1440` monitor to `1080p` saves `<0.2%` 2D shader load while making text blurry.
   - Instead, keep the secondary monitor at **native resolution** and drop its **Refresh Rate to `60Hz`** (or an exact integer divisor of the primary monitor, e.g., `60Hz` or `100Hz` alongside a `300Hz` primary, or `60Hz`/`120Hz` alongside a `240Hz` primary). This cuts secondary VRAM scanout bandwidth and Discord/browser repaint overhead by 60%+ while eliminating non-integer DWM VSync beat-frequency judder.
