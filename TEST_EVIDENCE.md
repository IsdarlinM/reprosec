# Test Evidence — ReproSec v0.5.0 Release Candidate

## Release-candidate review — 2026-08-08

The `agent/release-0.5.0` branch contains:

- SRIC 0.5 compatibility and no mandatory sibling-product runtime dependencies;
- evidence-native capsule research context for Sentinel Cases;
- formal RCAP 0.3 specification and corrected current schema pointer;
- `reprosec capabilities` and `/api/v1/capabilities`;
- standalone CLI/API/Web tests;
- recursive `--help`, `-h`, `COMMAND help` and invalid-option parser coverage for registered commands;
- Linux/Windows clean-install smoke definitions using only ReproSec + SRIC;
- Linux runtime uninstall that preserves capsules/configuration/user data;
- Standalone Product Contract and standardized release-evidence gate v2.

## Fresh execution status

**THE COMPLETE v0.5.0 TEST/RELEASE GATES HAVE NOT EXECUTED SUCCESSFULLY FOR THIS BRANCH.**

The repository cannot be mounted as a complete local checkout in the current runtime. The latest observed GitHub Actions run for the 0.5 branch concluded `startup_failure` and exposed zero jobs, so no pytest, installer, static-analysis or wheel result from that run is counted as evidence.

Tests being present in source is not a PASS result.

## Required exact-commit evidence

From installed/local sibling 0.5 checkouts:

```bash
python -m sric.standalone_gate --root reprosec
python sric-core/scripts/release-standalone-ecosystem.py --root .
python reprosec/scripts/release-gate.py
python sric-core/scripts/release-ecosystem.py --root .
```

Required machine-readable results:

- `reprosec/build/release-evidence/standalone-gate.json` = `PASS`;
- `reprosec/build/release-evidence/release-gate.json` = `PASS`;
- ecosystem standalone gate = `PASS`;
- ecosystem release gate = `PASS`.

Previous 0.4.x evidence remains a historical regression baseline only.
