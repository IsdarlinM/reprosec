# Web/CLI feature parity

ReproSec Capsule 0.5.6 mounts the shared SRIC Web Feature Workbench at `/workbench` and retains the advanced Web Command Console at `/console`.

The Workbench discovers `reprosec.cli_all` at runtime and generates a structured feature for every public command. Every positional argument, option, flag, paired boolean flag, repeated/count parameter and required/default/type/help attribute is represented in the Web catalog in the same order as the CLI. `/api/v1/workbench/coverage` reports whether the exact command/parameter contract is complete.

The native ReproSec dashboard remains the evidence-oriented quick view and now links directly to **All Features** and **Advanced Console**.

Neither surface is an operating-system shell. Structured Web fields are serialized to argv and execution uses the fixed `sric.web_console_runner`, `shell=False`, disabled stdin and no browser-controlled executable. Mutating commands require explicit approval and destructive commands require their typed approval phrase. ReproSec replay/capture Scope, Policy, rate-limit, target and approval checks remain authoritative.

Arguments and retained output are redacted, output is rendered as untrusted text, jobs are bounded/cancellable and output/status streams with SSE. Imported or remote content remains data, never instructions.

The standalone release tests walk every public CLI command with `--help`, verify its options/required arguments, compare every ordered CLI parameter against the Workbench schema, and verify the native dashboard navigation. Destructive actions are gate-tested instead of being executed merely to satisfy coverage.

See the shared SRIC documents `docs/web/feature-workbench.md` and `docs/web/cli-parity.md` for the common contract.
