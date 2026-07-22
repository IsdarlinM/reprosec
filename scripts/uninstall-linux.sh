#!/usr/bin/env sh
set -eu
rm -f "${HOME}/.local/bin/reprosec"; rm -rf "${HOME}/.local/share/reprosec"
echo "ReproSec runtime removed. User-created capsules were not deleted."
