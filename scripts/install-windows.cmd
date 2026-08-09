@echo off
setlocal EnableExtensions
set "PROJECT=ReproSec Capsule"
set "CMD=reprosec"
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "CONSTRAINTS=%REPO_ROOT%\requirements\runtime-py311.lock"
set "FIRST_PARTY=%REPO_ROOT%\requirements\first-party.txt"
set "INSTALL_ROOT=%LOCALAPPDATA%\ReproSec"
set "VENV=%INSTALL_ROOT%\venv"
set "BIN_DIR=%USERPROFILE%\.local\bin"
where py >nul 2>&1
if not errorlevel 1 (set "PY_CMD=py -3.11") else (where python >nul 2>&1 || (echo Python 3.11+ is required.& exit /b 2)& set "PY_CMD=python")
%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (echo Python 3.11+ is required.& exit /b 2)
if not exist "%INSTALL_ROOT%" mkdir "%INSTALL_ROOT%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if not exist "%VENV%\Scripts\python.exe" %PY_CMD% -m venv "%VENV%" || exit /b 1
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip || exit /b 1
if defined SRIC_CORE_SOURCE (
  if not exist "%SRIC_CORE_SOURCE%\pyproject.toml" (echo SRIC_CORE_SOURCE is invalid.& exit /b 3)
  "%VENV%\Scripts\python.exe" -m pip install --upgrade --force-reinstall -c "%CONSTRAINTS%" "%SRIC_CORE_SOURCE%" || (echo Failed to repair SRIC Core.& exit /b 3)
) else (
  if not exist "%FIRST_PARTY%" (echo Missing first-party dependency manifest: %FIRST_PARTY%& exit /b 3)
  "%VENV%\Scripts\python.exe" -m pip install --upgrade --force-reinstall -c "%CONSTRAINTS%" -r "%FIRST_PARTY%" || (echo Failed to repair Sentinel Forge first-party dependencies.& exit /b 3)
)
"%VENV%\Scripts\python.exe" -m pip install --upgrade --force-reinstall -c "%CONSTRAINTS%" "%REPO_ROOT%" || (echo Installation failed after dependency bootstrap.& exit /b 3)
"%VENV%\Scripts\python.exe" -m pip check || (echo Installed dependency graph is inconsistent.& exit /b 3)
"%VENV%\Scripts\python.exe" -c "import importlib.metadata as m; import sric.web_console, sric.web_workbench; v=tuple(int(x) for x in m.version('sric-core').split('.')[:3]); raise SystemExit(0 if (0,5,7) <= v < (0,6,0) else 1)" || (echo SRIC Core runtime integrity check failed. Required ^>=0.5.7,^<0.6.& exit /b 3)
>"%BIN_DIR%\%CMD%.cmd" echo @"%VENV%\Scripts\%CMD%.exe" %%*
for /f "tokens=2,*" %%A in ('reg query HKCU\Environment /v Path 2^>nul ^| findstr /I "Path"') do set "USER_PATH=%%B"
echo ;%USER_PATH%; | find /I ";%BIN_DIR%;" >nul
if errorlevel 1 (if defined USER_PATH (setx PATH "%USER_PATH%;%BIN_DIR%" >nul) else (setx PATH "%BIN_DIR%" >nul))
"%VENV%\Scripts\%CMD%.exe" doctor || exit /b 1
"%VENV%\Scripts\%CMD%.exe" capabilities || exit /b 1
"%VENV%\Scripts\%CMD%.exe" --help >nul || exit /b 1
"%VENV%\Scripts\%CMD%.exe" -h >nul || exit /b 1
echo %PROJECT% installed/repaired successfully in standalone mode.
exit /b 0
