#!/usr/bin/env sh
set -eu

PROJECT="ReproSec Capsule"
CMD="reprosec"
INSTALL_ROOT="${HOME}/.local/share/reprosec"
VENV="$INSTALL_ROOT/venv"
BIN_DIR="${HOME}/.local/bin"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CONSTRAINTS="$REPO_ROOT/requirements/runtime-py311.lock"
FIRST_PARTY="$REPO_ROOT/requirements/first-party.txt"

if [ "$(id -u)" = "0" ] && [ "${ALLOW_ROOT_INSTALL:-0}" != "1" ]; then
  echo "Refusing root install by default." >&2
  exit 2
fi

PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1 || {
  echo "Python 3.11+ is required." >&2
  exit 2
}

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
[ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel || {
  echo "Failed to bootstrap pip/setuptools/wheel." >&2
  exit 3
}

# Resolve ReproSec and its explicit first-party SRIC source in one transaction.
# This prevents pip from trying to discover the intentionally unpublished
# sric-core package from PyPI during a forced repair.
if [ -n "${SRIC_CORE_SOURCE:-}" ]; then
  [ -f "$SRIC_CORE_SOURCE/pyproject.toml" ] || {
    echo "SRIC_CORE_SOURCE does not point to a valid sric-core checkout." >&2
    exit 3
  }
  "$VENV/bin/python" -m pip install --upgrade --force-reinstall -c "$CONSTRAINTS" "$SRIC_CORE_SOURCE" "$REPO_ROOT" || {
    echo "Atomic ReproSec/SRIC installation failed." >&2
    exit 3
  }
else
  [ -f "$FIRST_PARTY" ] || {
    echo "Missing first-party dependency manifest: $FIRST_PARTY" >&2
    exit 3
  }
  "$VENV/bin/python" -m pip install --upgrade --force-reinstall -c "$CONSTRAINTS" -r "$FIRST_PARTY" "$REPO_ROOT" || {
    echo "Atomic ReproSec/SRIC installation failed." >&2
    exit 3
  }
fi

"$VENV/bin/python" -m pip check || {
  echo "Installed dependency graph is inconsistent." >&2
  exit 3
}
"$VENV/bin/python" -c 'import importlib.metadata as m; import sric.web_console, sric.web_workbench; v=tuple(int(x) for x in m.version("sric-core").split(".")[:3]); raise SystemExit(0 if (0,5,7) <= v < (0,6,0) else 1)' || {
  echo "SRIC Core runtime integrity check failed; required >=0.5.7,<0.6." >&2
  exit 3
}

ln -sfn "$VENV/bin/$CMD" "$BIN_DIR/$CMD"
PROFILE="${HOME}/.profile"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
touch "$PROFILE"
grep -F "$PATH_LINE" "$PROFILE" >/dev/null 2>&1 || printf '\n# Sentinel Forge tools\n%s\n' "$PATH_LINE" >> "$PROFILE"

"$VENV/bin/$CMD" doctor
"$VENV/bin/$CMD" capabilities
"$VENV/bin/$CMD" --help >/dev/null
"$VENV/bin/$CMD" -h >/dev/null
"$VENV/bin/$CMD" help >/dev/null
printf '%s installed/repaired successfully in standalone mode.\n' "$PROJECT"
printf 'Command: %s\n' "$CMD"
