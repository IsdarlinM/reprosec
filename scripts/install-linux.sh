#!/usr/bin/env sh
set -eu
PROJECT="ReproSec Capsule"; CMD="reprosec"; INSTALL_ROOT="${HOME}/.local/share/reprosec"; VENV="$INSTALL_ROOT/venv"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd); REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd); CONSTRAINTS="$REPO_ROOT/requirements/runtime-py311.lock"; FIRST_PARTY="$REPO_ROOT/requirements/first-party.txt"
[ "$(id -u)" != "0" ] || [ "${ALLOW_ROOT_INSTALL:-0}" = "1" ] || { echo "Refusing root install by default." >&2; exit 2; }
if [ -n "${PYTHON:-}" ]; then command -v "$PYTHON" >/dev/null 2>&1 || exit 2; elif command -v python3 >/dev/null 2>&1; then PYTHON=python3; elif command -v python >/dev/null 2>&1; then PYTHON=python; else echo "Python 3.11+ is required." >&2; exit 2; fi
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' || { echo "Python 3.11+ is required." >&2; exit 2; }
BIN_DIR="${HOME}/.local/bin"; if [ -n "${PREFIX:-}" ] && [ -d "${PREFIX}/bin" ] && [ -w "${PREFIX}/bin" ]; then case ":${PATH:-}:" in *":${PREFIX}/bin:"*) BIN_DIR="${PREFIX}/bin" ;; esac; fi; mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
if [ -x "$VENV/bin/python" ]; then "$VENV/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1 || rm -rf "$VENV"; elif [ -e "$VENV" ]; then rm -rf "$VENV"; fi
[ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV" || exit 3; "$VENV/bin/python" -m pip install --upgrade pip setuptools wheel || exit 3
if [ -n "${SRIC_CORE_SOURCE:-}" ]; then [ -f "$SRIC_CORE_SOURCE/pyproject.toml" ] || exit 3; "$VENV/bin/python" -m pip install --upgrade -c "$CONSTRAINTS" "$SRIC_CORE_SOURCE" "$REPO_ROOT"; else [ -f "$FIRST_PARTY" ] || exit 3; "$VENV/bin/python" -m pip install --upgrade -c "$CONSTRAINTS" -r "$FIRST_PARTY" "$REPO_ROOT"; fi || { echo "Atomic ReproSec/SRIC installation failed." >&2; exit 3; }
"$VENV/bin/python" -m pip check || exit 3; "$VENV/bin/python" -c 'import sric.web_console, sric.web_workbench' || exit 3
ln -sfn "$VENV/bin/$CMD" "$BIN_DIR/$CMD"; case ":${PATH:-}:" in *":$BIN_DIR:"*) ;; *) PROFILE="${HOME}/.profile"; PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'; touch "$PROFILE"; grep -F "$PATH_LINE" "$PROFILE" >/dev/null 2>&1 || printf '\n# Sentinel Forge tools\n%s\n' "$PATH_LINE" >> "$PROFILE" ;; esac
SENTINEL_BANNER=never "$VENV/bin/$CMD" doctor >/dev/null; SENTINEL_BANNER=never "$VENV/bin/$CMD" capabilities >/dev/null; SENTINEL_BANNER=never "$VENV/bin/$CMD" --help >/dev/null; SENTINEL_BANNER=never "$VENV/bin/$CMD" -h >/dev/null; SENTINEL_BANNER=never "$VENV/bin/$CMD" help >/dev/null
printf '%s installed/repaired successfully in standalone mode.\nCommand: %s\n' "$PROJECT" "$CMD"
