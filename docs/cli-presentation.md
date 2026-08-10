# CLI presentation

ReproSec Capsule 0.5.10 uses the shared Sentinel Forge CLI presentation contract from SRIC Core.

Interactive console sessions show a subdued green ASCII banner ordered as `ReproSec Capsule :: v0.5.10`, `Developer: IsdarlinM`, then the concise purpose statement. The banner is written to interactive stderr, keeping stdout suitable for JSON, exports, redirection, and automation.

Use `reprosec --no-color COMMAND` to disable ANSI/Rich colors. The installed console entrypoint also normalizes `reprosec COMMAND --no-color`. The standard `NO_COLOR` environment variable is honored.

Installer-internal CLI smokes use `SENTINEL_BANNER=never` and a temporary diagnostic log so successful installs do not print the banner repeatedly; the captured output is emitted if validation fails.

The public help contract includes `reprosec --help`, `reprosec -h`, `reprosec help`, `reprosec COMMAND --help`, `reprosec COMMAND -h`, and `reprosec COMMAND help`. The release regression suite walks every public command and checks its ordered CLI parameters against the Web Feature Workbench schema.

Typer/Rich command and help presentation is colorized by default. `--no-color` changes presentation only; it does not alter capsule contents, evidence, replay behavior, policy decisions, update verification, Web Feature Workbench/Command Console behavior, or API responses.
