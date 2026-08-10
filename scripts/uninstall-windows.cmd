@echo off
setlocal EnableExtensions
set "PROJECT=ReproSec Capsule"
set "CMD=reprosec"
set "INSTALL_ROOT=%LOCALAPPDATA%\ReproSec"
set "VENV=%INSTALL_ROOT%\venv"
set "BIN_DIR=%USERPROFILE%\.local\bin"

if exist "%BIN_DIR%\%CMD%.cmd" del /q "%BIN_DIR%\%CMD%.cmd" >nul 2>&1
if exist "%VENV%" rmdir /s /q "%VENV%"
if exist "%INSTALL_ROOT%\install-check.log" del /q "%INSTALL_ROOT%\install-check.log" >nul 2>&1

rem BIN_DIR is shared by Sentinel Forge tools, so it remains in PATH.
rem Capsules, configuration, workspaces and evidence are intentionally preserved.
echo %PROJECT% runtime removed. User data was preserved.
exit /b 0
