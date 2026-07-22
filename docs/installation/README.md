# Installation

ReproSec v0.3 depends on SRIC Core v0.3. In this source workspace, the installers detect the sibling `sric-core` project and install it first. Runtime dependency constraints are stored in `requirements/runtime-py311.lock` and release artifacts remain independently protected by signed manifests and SHA-256 verification.

Linux: `./scripts/install-linux.sh`; Windows: `scripts\install-windows.cmd`. Verify with `reprosec doctor`.
