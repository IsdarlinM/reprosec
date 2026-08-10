# ReproSec Capsule

```text
ReproSec Capsule :: v0.5.12
Developer: IsdarlinM

Capture, sanitize, replay, and package reproducible security evidence.
```

ReproSec is the reference implementation of `.rcap`: an open, deterministic container for portable and reproducible security evidence.

> **AI proposes. Evidence proves. Humans control.**

## Standalone by design

ReproSec is independently installable and useful. It requires **SRIC Core >=0.5.12,<0.6** for common evidence/provenance/policy/Web/runtime primitives, but AuthTwin, FossilScope, TrustBoundary Mapper and Exposure DNA are never required for capture, import, replay, validation, reporting, CLI, API or Web UI.

```bash
reprosec doctor
reprosec capabilities
```

Compatible Sentinel Forge products add optional capabilities through shared contracts and RCAP evidence; they are not runtime prerequisites.

## Implemented

- RCAP actors, sessions, secret references, network/validation records and compatibility material for older RCAP schemas;
- deterministic `.rcap` packing, SHA-256 manifests, Ed25519 signing and verification;
- safe extraction with traversal, symlink, entry-count, decompression-size and compression-ratio controls;
- HAR, raw HTTP, constrained non-executing curl, Burp and ZAP imports;
- structured redaction with preview before persistence;
- explicit variables and ephemeral bindings; unresolved values fail closed;
- response evidence with hashes, size, truncation state and retained-body limits;
- DNS-pinned direct replay preserving hostname, SNI and certificate verification;
- gate order `Scope -> Policy -> Rate Limit -> Approval -> Executor` with redirect revalidation;
- timeline, evidence lineage and observed actor/operation matrix;
- authorized bounded HTTP capture, loopback proxy and browser-event recorder; CONNECT/TLS is metadata-only by default;
- evidence-native research context linking scope snapshots, policy decisions, validation recipes, tool provenance and counter-evidence;
- local FastAPI API, responsive Web UI and offline synthetic demo;
- SRIC workspaces, graph, lineage, notebook and evidence primitives;
- zero-config product update flow with same-version `update --force`, rollback and first-party runtime repair;
- exact SRIC version/module compatibility checks in `doctor` and the local API;
- full Web Feature Workbench with every public ReproSec CLI command and argument represented as structured responsive controls;
- JSON-safe shared Web command catalog generation;
- structured redacted HTTP 503 catalog failures, bounded Web child reaping, SSE-safe retired-job retention and persisted Job Engine secret redaction from SRIC 0.5.12;
- degraded Web mode preserving the native dashboard with actionable compatibility 503s;
- advanced Web Command Console with fixed-runner execution, exact CLI-tree parity and real-time jobs;
- professional Rich/Typer terminal presentation with subdued green banner and `--no-color` support.

## Standalone install and repair

Linux / Termux:

```bash
./scripts/install-linux.sh
reprosec doctor
reprosec capabilities
```

Windows:

```cmd
scripts\install-windows.cmd
reprosec doctor
reprosec capabilities
```

The installer pins SRIC Core to immutable signed main commit `4dd0ad417e55fc76fb67d582ec50234bffff2876` and resolves that explicit first-party source in the same pip transaction as ReproSec. `SRIC_CORE_SOURCE=/path/to/sric-core` remains an explicit development/release-validation override.

The repair path preserves capsules, configuration and workspaces. It validates host Python and any existing venv; a stale/incomplete/broken environment rebuilds only the isolated ReproSec venv. It bootstraps `pip`, `setuptools` and `wheel`, runs `pip check`, imports `sric.web_console`, `sric.web_workbench`, `sric.web_catalog` and `sric.web_runtime`, requires SRIC `>=0.5.12,<0.6`, and smoke-tests doctor/capabilities plus all root help aliases before reporting success.

Installer-internal smokes use `SENTINEL_BANNER=never` and a temporary validation log. Successful installation therefore does not repeat the banner; failed smokes print captured diagnostics. Normal installation does not use `--force-reinstall`.

Termux prefers a writable `$PREFIX/bin` already present in `PATH`; standard Linux falls back to `~/.local/bin`. Windows uses SRIC's registry-backed `sric.install_path` helper rather than `setx` and accepts any Python 3 interpreter satisfying `>=3.11`.

## CLI presentation and help contract

Interactive terminals display `ReproSec Capsule :: v0.5.12`, `Developer: IsdarlinM`, then the purpose statement. Use `reprosec --no-color COMMAND`, `reprosec COMMAND --no-color`, or `NO_COLOR=1` for plain output.

Supported help forms:

```text
reprosec --help
reprosec -h
reprosec help
reprosec COMMAND --help
reprosec COMMAND -h
reprosec COMMAND help
```

Unexpected operational exceptions are redacted/contained by SRIC. `SENTINEL_DEBUG=1` is an explicit developer-only opt-in for raw local exception propagation.

## First five minutes

```bash
reprosec doctor
reprosec capabilities
reprosec demo --output demo-capsule
reprosec inspect demo-capsule
reprosec timeline demo-capsule
reprosec matrix demo-capsule
reprosec conformance demo-capsule
reprosec pack demo-capsule --output demo.rcap
reprosec verify demo.rcap
reprosec report demo-capsule --output report.md --format md
```

## Import evidence

```bash
reprosec init case1 --title "Authorized test case"
reprosec import har session.har --capsule case1
reprosec import raw request.txt --capsule case1
reprosec redact case1
```

Imported commands/files are untrusted data and are never executed as instructions.

## Safe replay

```bash
reprosec replay case1 REQ-... --allow '*.example.com' --allow-method GET
```

Authorized mutating requests additionally require method scope and human approval.

## Web and API

`reprosec web` serves the native evidence dashboard plus:

- `/workbench` — every public `reprosec.cli_all` command/parameter as a structured Web form;
- `/console` — advanced argv-oriented fixed-runner console;
- `/api/v1/runtime-compatibility` — exact shared-runtime diagnostic.

The Workbench schema is generated from the installed CLI tree; parity coverage fails when a command or parameter disappears from Web representation. Command metadata is normalized to JSON-safe primitives. A catalog-construction failure returns a bounded/redacted HTTP 503 rather than an opaque HTTP 500.

Neither shared surface is an operating-system shell. Execution uses `shell=False`, disabled stdin, CSRF protection, secret redaction, bounded/cancellable jobs, approval gates and SSE output. Timed-out child commands use bounded terminate/kill/wait handling plus background reaping if needed; recently pruned terminal jobs remain briefly available to active status/SSE readers. ReproSec's Scope, Policy, rate-limit, target validation and approval gates remain authoritative for capture/replay and all other active operations.

## Updates and shared-runtime repair

```bash
reprosec update --check
reprosec update
reprosec update --force
```

Supported stale SRIC runtimes are advanced through immutable GitHub-signature-verified snapshots one release at a time from 0.5.5 through 0.5.12, avoiding unsafe rollback-metadata jumps. A same-version corrupt 0.5.12 runtime is repaired from the fixed signed 0.5.12 snapshot. No blind `git pull` fallback is used.

The SRIC official update channel may remain on the previous fully gated release while 0.5.12 exact-commit gates are blocked; ReproSec's first-party pin/repair chain uses fixed verified commits independently of that moving channel.

## Validation gates

```bash
python -m sric.standalone_gate --root .
python scripts/release-gate.py
```

The 0.5.12 standalone runtime regression walks every public ReproSec command, root/subcommand `--help`, `-h` and trailing `help`, and exact ordered CLI/Web parameter parity. Existing suites cover Web Console/Workbench pages/assets/catalogs/coverage, local GET/POST APIs, RCAP parsers/importers, capture/replay, scope/DNS pinning, redaction, assertions, reports, fuzz/security and destructive-action gates.

`TEST_EVIDENCE.md` is authoritative for actual execution. The shared SRIC 0.5.12 focused runtime harness completed four targeted regressions after first exposing and fixing a background-reaper return-code race. GitHub-hosted runners are currently blocked by an account billing lock; zero-step workflows are not PASS and do not prove ReproSec's full exact-commit release gate.

## Uninstall

```bash
./scripts/uninstall-linux.sh
```

Runtime files are removed while capsules, configuration and other user data are preserved.

## Security and privacy defaults

- Telemetry: **OFF**.
- Cloud AI: **OFF**.
- External uploads: **OFF**.
- Environment HTTP proxies: **ignored by replay**.
- Non-loopback Web/API exposure: **denied**.
- Imported content: **untrusted data, never instructions**.
- Required replay secrets: **ephemeral bindings or approved secret providers**.

Use ReproSec only on systems you own or are explicitly authorized to test. Apache-2.0.
