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
set "PY_CMD="
where py >nul 2>&1
if not errorlevel 1 (py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1 & if not errorlevel 1 set "PY_CMD=py -3")
if not defined PY_CMD (where python >nul 2>&1 & if not errorlevel 1 (python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1 & if not errorlevel 1 set "PY_CMD=python"))
if not defined PY_CMD (echo Python 3.11+ is required.& exit /b 2)
if not exist "%INSTALL_ROOT%" mkdir "%INSTALL_ROOT%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if exist "%VENV%\Scripts\python.exe" ("%VENV%\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1 || rmdir /s /q "%VENV%") else if exist "%VENV%" rmdir /s /q "%VENV%"
if not exist "%VENV%\Scripts\python.exe" %PY_CMD% -m venv "%VENV%" || exit /b 3
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel || exit /b 3
if defined SRIC_CORE_SOURCE (
  if not exist "%SRIC_CORE_SOURCE%\pyproject.toml" exit /b 3
  "%VENV%\Scripts\python.exe" -m pip install --upgrade -c "%CONSTRAINTS%" "%SRIC_CORE_SOURCE%" "%REPO_ROOT%" || exit /b 3
) else (
  if not exist "%FIRST_PARTY%" exit /b 3
  "%VENV%\Scripts\python.exe" -m pip install --upgrade -c "%CONSTRAINTS%" -r "%FIRST_PARTY%" "%REPO_ROOT%" || exit /b 3
)
"%VENV%\Scripts\python.exe" -m pip check || exit /b 3
"%VENV%\Scripts\python.exe" -c "import importlib.metadata as m; import sric.web_console, sric.web_workbench, sric.web_security_workspace, sric.web_catalog, sric.web_runtime; v=tuple(int(x) for x in m.version('sric-core').split('.')[:3]); raise SystemExit(0 if (0,5,14)<=v<(0,6,0) else 1)" || (echo SRIC Core runtime integrity check failed. Required ^>=0.5.14,^<0.6.& exit /b 3)
>"%BIN_DIR%\%CMD%.cmd" echo @"%VENV%\Scripts\%CMD%.exe" %%*
"%VENV%\Scripts\python.exe" -m sric.install_path "%BIN_DIR%" || exit /b 3
set "SENTINEL_BANNER=never"
set "CHECK_LOG=%INSTALL_ROOT%\install-check.log"
>"%CHECK_LOG%" type nul
"%VENV%\Scripts\%CMD%.exe" version >>"%CHECK_LOG%" 2>&1 || goto :validation_failed
"%VENV%\Scripts\%CMD%.exe" doctor >>"%CHECK_LOG%" 2>&1 || goto :validation_failed
"%VENV%\Scripts\%CMD%.exe" capabilities >>"%CHECK_LOG%" 2>&1 || goto :validation_failed
"%VENV%\Scripts\%CMD%.exe" --help >>"%CHECK_LOG%" 2>&1 || goto :validation_failed
"%VENV%\Scripts\%CMD%.exe" -h >>"%CHECK_LOG%" 2>&1 || goto :validation_failed
"%VENV%\Scripts\%CMD%.exe" help >>"%CHECK_LOG%" 2>&1 || goto :validation_failed
del /q "%CHECK_LOG%" >nul 2>&1
echo %PROJECT% installed/repaired successfully in standalone mode.
exit /b 0
:validation_failed
echo Installation validation failed.
type "%CHECK_LOG%"
exit /b 4
