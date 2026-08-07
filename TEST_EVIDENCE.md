# Test Evidence — ReproSec v0.4.1

## QA pass — 2026-08-07

Freshly executed in the current local runtime:

- Sentinel Forge cross-product high-risk regression matrix including ReproSec capsule minimization, replay stability and passive protocol records: **7/7 matrix tests passed**;
- Python `compileall` over the reconstructed corrected modules: **PASS**;
- branch comparison against `main`: branch is ahead and **0 commits behind** at the time of this audit.

Current-source review and regression tests added in this pass cover:

- explicit minimization roots and transitive retention;
- case-insensitive HTTP `Content-Type` handling;
- invalid regex rejection;
- protocol subtype discriminators and WebSocket CLOSE metadata;
- stability/protocol/minimization API errors returning controlled 422 responses;
- `capsule-analysis` being registered in the installed CLI;
- precision/protocol/capsule CLI validation returning controlled exit codes instead of tracebacks;
- recursive `--help`, `-h` and trailing `COMMAND help` coverage through the final entrypoint;
- `reprosec web` serving the vNext API, including capsule-analysis routes;
- public Python exports for capsule comparison/minimization.

## Current release-gate status

**FULL CURRENT REPOSITORY GATE NOT EXECUTABLE IN THIS RUNTIME.**

The repository is private and this runtime cannot materialize a complete checkout from GitHub; individual authenticated blobs are available only through the connector. Ruff, mypy, `build` and `pip-audit` are unavailable and cannot be installed from the environment package index. No GitHub Actions, Codespaces or paid/hosted GitHub execution was used.

The complete exact-commit gate must still be run from a sibling local checkout before treating v0.4.1 as a fully validated release:

```bash
python -m pip install -e ../sric-core
python -m pip install -e '.[dev]'
python scripts/release-gate.py
```

## Previous validated baseline

The previous v0.4.0 state was recorded on 2026-07-22 with **68 pytest tests passed**, compileall/security scan/CLI help/synthetic smoke/build/isolated wheel smoke all PASS. Those results are a regression baseline only and do not prove v0.4.1.
