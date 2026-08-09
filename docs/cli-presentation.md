# CLI presentation

ReproSec Capsule 0.5.4 uses the shared Sentinel Forge CLI presentation contract from SRIC Core.

Interactive console sessions show a subdued green ASCII banner ordered as `ReproSec Capsule :: v0.5.4`, `Developer: IsdarlinM`, then the concise purpose statement. The banner is written to interactive stderr, keeping stdout suitable for JSON, exports, redirection, and automation.

Use `reprosec --no-color COMMAND` to disable ANSI/Rich colors. The installed console entrypoint also normalizes `reprosec COMMAND --no-color`. The standard `NO_COLOR` environment variable is honored.

Typer/Rich command and help presentation is colorized by default. `--no-color` changes presentation only; it does not alter capsule contents, evidence, replay behavior, policy decisions, update verification, Web Command Console behavior, or API responses.
