#!/usr/bin/env sh
set -eu
INSTALL_ROOT="${HOME}/.local/share/reprosec"
BIN="${HOME}/.local/bin/reprosec"
rm -f "$BIN"
rm -rf "$INSTALL_ROOT/venv"
echo "Removed ReproSec runtime. Capsules, configuration and other user data under $INSTALL_ROOT were preserved."
