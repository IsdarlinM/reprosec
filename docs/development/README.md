# Development

Install sibling SRIC Core, then ReproSec development dependencies. Run `pytest`, `ruff check src tests`, `mypy --strict src/reprosec`, `python -m compileall -q src`, and `python scripts/security-scan.py`.

The Web UI is dependency-light static source under `web/`; packaged assets under `src/reprosec/webdist/` must remain byte-identical to their source counterparts. CI verifies this with `cmp`.

Importer and replay changes require adversarial/security tests, including scope/SSRF, DNS pinning, redirect revalidation, archive safety, response limits, redaction, and unresolved-variable fail-closed behavior.
