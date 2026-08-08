# CLI presentation

ReproSec Capsule 0.5.2 uses the shared Sentinel Forge CLI presentation contract from SRIC Core.

Interactive console sessions show a subdued green ASCII banner with the product name, a one-line purpose statement, and `IsdarlinM :: v0.5.2`. The banner is written to interactive stderr, keeping stdout suitable for JSON, exports, redirection, and automation.

Use `reprosec --no-color COMMAND` to disable ANSI/Rich colors. The installed console entrypoint also normalizes `reprosec COMMAND --no-color`. The standard `NO_COLOR` environment variable is honored.

Typer/Rich command and help presentation is colorized by default. `--no-color` changes presentation only; it does not alter capsule contents, evidence, replay behavior, policy decisions, or API responses.
