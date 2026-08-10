# Installation and uninstallation

| Platform | Install | Uninstall |
|---|---|---|
| Linux / Termux | `sh scripts/install-linux.sh` | `sh scripts/uninstall-linux.sh` |
| Windows | `scripts\install-windows.cmd` | `scripts\uninstall-windows.cmd` |

The Windows uninstaller removes the `reprosec.cmd` shim and isolated ReproSec venv. It does not delete the shared `%USERPROFILE%\.local\bin` PATH entry. Capsules, configuration, workspaces and evidence are preserved by default. Linux follows the same data-preservation contract.
