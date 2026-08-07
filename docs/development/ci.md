# Local release validation

ReproSec does not depend on GitHub Actions or another hosted CI service. Run the cross-platform release gate from an isolated development environment:

```bash
python -m pip install -e ../sric-core
python -m pip install -e '.[dev]'
python scripts/release-gate.py
```

The full gate performs Python compilation, Ruff, strict mypy, all pytest suites, the project security scan, dependency audit, SBOM generation, wheel/source build, isolated wheel installation and CLI `--help`/`-h` smoke checks. It writes machine-readable evidence to `build/release-evidence/release-gate.json` and records SHA-256 hashes for release artifacts.

For a development-only pass:

```bash
python scripts/release-gate.py --quick
```

For an offline wheel smoke that does not resolve dependencies:

```bash
python scripts/release-gate.py --offline
```

A release must not be announced if the full report status is `FAIL`, required release tools are missing, Web source/package integrity checks have not been run, or the report does not correspond to the exact source commit being released.

No target credentials, capsule secrets, workspace data or production secrets are required by this process.
