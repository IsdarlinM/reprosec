# Test Evidence — ReproSec v0.5.0 Release Candidate

## Release-candidate review — 2026-08-08

The `agent/release-0.5.0` branch contains the ReproSec 0.5 changes under review:

- SRIC 0.5 compatibility;
- evidence-native capsule research context for Sentinel Cases;
- scope snapshots, policy decisions, validation recipes, tool provenance and counter-evidence references;
- destructive-decision approval guards;
- formal RCAP 0.3 specification and corrected current schema pointer;
- 0.5 regression tests and standardized release-evidence gate v2.

## Fresh execution status

**THE COMPLETE v0.5.0 RELEASE GATE HAS NOT BEEN EXECUTED SUCCESSFULLY FOR THIS BRANCH.**

The private repository is accessible through the GitHub connector but cannot be mounted as a complete local checkout in this runtime. GitHub Actions currently terminates at `startup_failure` before test jobs start; the same infrastructure symptom is present in earlier ecosystem workflow runs, so it is not treated as test evidence.

## Required release evidence

Run the coordinated release train from sibling 0.5 checkouts:

```bash
python sric-core/scripts/release-ecosystem.py --root .
```

The ecosystem gate supplies exact unreleased internal wheels through a local wheelhouse, then executes ReproSec's static checks, pytest, security/eval hooks, dependency audit, SBOM generation, build and isolated CLI wheel smoke.

Do not merge/tag ReproSec 0.5 until its exact-commit `release-gate.json` and the ecosystem `ecosystem-release-gate.json` both report `PASS`.

Previous 0.4.x evidence remains a historical regression baseline only.
