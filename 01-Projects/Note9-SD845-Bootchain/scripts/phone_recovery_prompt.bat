@echo off
setlocal EnableExtensions
rem ============================================================
rem  phone_recovery_prompt.bat   EVEATLAS Note9-SD845-Bootchain
rem  Asks the operator to put the SM-N960U into RECOVERY MODE
rem  (Vol Up + Bixby + Power -> blue "Android Recovery" screen),
rem  then waits for adb to report the device in recovery.
rem  READ-ONLY tool: never flashes, never writes the device.
rem
rem  Usage:  double-click, or  phone_recovery_prompt.bat
rem  Test:   phone_recovery_prompt.bat --self-test  (skips popup+adb)
rem  Exit:   0 = recovery detected   1 = manual confirm (no adb)
rem          2 = not detected in 5 min
rem  Log:    analysis\device\recovery-prompt.log  (git-ignored)
rem ============================================================

set "SCRIPT_DIR=%~dp0"
set "PROJ_DIR=%SCRIPT_DIR%.."
set "LOGDIR=%PROJ_DIR%\analysis\device"
set "LOG=%LOGDIR%\recovery-prompt.log"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"
if not exist "%LOG%" echo [%date% %time%] log initialized > "%LOG%"

if /I "%~1"=="--self-test" (
  echo [%date% %time%] self-test: popup + adb detection skipped >> "%LOG%"
  echo [self-test ok] log at %LOG%
  exit /b 0
)

rem ---------- 1) visible alert with instructions ----------
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Add-Type -AssemblyName System.Windows.Forms; $m=[string]::Join([char]10, @('NOTE9 (SM-N960U) - RECOVERY MODE REQUESTED','','1) Power the phone OFF.','2) Hold Volume Up + Bixby + Power together.','3) Release all three keys when the SAMSUNG logo appears.','4) You should land on the blue Android Recovery screen.','','If it boots normally you pressed Volume Down (Download Mode) instead - retry.','','Press OK when the phone is on the recovery screen.','I will watch for it over adb for up to 5 minutes.')) -replace '\r',''; [System.Windows.Forms.MessageBox]::Show($m,'NOTE9-RECOVERY-REQ','OK')" >nul 2>&1
echo [%date% %time%] prompt shown, waiting for adb detection >> "%LOG%"

rem ---------- 2) locate adb (PATH, then standard SDK spot) ----------
set "ADB="
for %%X in (adb.exe) do set "ADB=%%~$PATH:X"
if not defined ADB if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" set "ADB=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
if not defined ADB goto noadb

"%ADB%" start-server >nul 2>&1
set /a TRIES=0
:waitloop
"%ADB%" devices | findstr /r /c:"recovery" >nul
if not errorlevel 1 goto found
set /a TRIES+=1
if %TRIES% GEQ 30 goto notfound
timeout /t 10 /nobreak >nul
goto waitloop

:found
echo [%date% %time%] DETECTED: adb reports device in recovery >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('RECOVERY MODE DETECTED over adb. Keep the phone there - do not wipe, flash or reboot unless asked.','NOTE9-OK','OK')" >nul 2>&1
exit /b 0

:notfound
echo [%date% %time%] NOT detected after 5 minutes >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Could not detect the phone in recovery within 5 minutes. Check: USB cable/port, Samsung driver, and that it really is on the blue Android Recovery screen. You can rerun this script.','NOTE9-TIMEOUT','OK')" >nul 2>&1
exit /b 2

:noadb
echo [%date% %time%] adb not found - manual confirm mode >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Add-Type -AssemblyName System.Windows.Forms; $m=[string]::Join([char]10, @('adb was NOT found (PATH + %LOCALAPPDATA%\Android\Sdk\platform-tools both checked).','','Detection will be skipped. Put the phone in Recovery Mode now (Vol Up + Bixby + Power until the SAMSUNG logo, release, land on the blue screen) and press OK when it is there.')) -replace '\r',''; [System.Windows.Forms.MessageBox]::Show($m,'NOTE9-MANUAL','OK')" >nul 2>&1
echo [%date% %time%] operator confirmed manually >> "%LOG%"
exit /b 1