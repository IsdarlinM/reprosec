# Development

Install sibling SRIC Core, then ReproSec development dependencies. Run `pytest`, `ruff check src tests`, `mypy --strict`, and `python -m compileall -q src`. The Web UI is dependency-light static source under `web/`; CI verifies it is byte-identical to packaged `src/reprosec/webdist/` assets. Importers, capture, replay and RCAP changes require adversarial/security tests.
