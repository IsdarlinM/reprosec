# ReproSec Capsule

```text
ReproSec Capsule :: v0.5.13
Developer: IsdarlinM

Capture, sanitize, replay, and package reproducible security evidence.
```

ReproSec is the reference implementation of `.rcap`: an open, deterministic container for portable and reproducible security evidence.

> **AI proposes. Evidence proves. Humans control.**

## Standalone by design

ReproSec is independently installable and useful. It requires **SRIC Core >=0.5.13,<0.6** for common evidence/provenance/policy/Web/runtime primitives, but AuthTwin, FossilScope, TrustBoundary Mapper and Exposure DNA are never required for capture, import, replay, validation, reporting, CLI, API or Web UI.

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
- guided Web Security Console with every public ReproSec CLI capability represented as operation cards and typed responsive controls;
- checkboxes/tri-state selectors for flags, combo/select controls for closed choices, numeric/path controls, repeated-value controls and protected sensitive fields;
- JSON-safe shared Web capability catalog generation;
- structured redacted HTTP 503 catalog failures, bounded Web child reaping, SSE-safe retired-job retention and persisted Job Engine secret redaction from SRIC 0.5.13;
- degraded Web mode preserving the native dashboard with actionable compatibility 503s;
- fixed-runner execution with exact CLI-tree parity and real-time jobs while keeping free-form command/argv entry out of the user interface;
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

The installer pins SRIC Core to immutable GitHub-verified commit `bd90fe668e4a2a23c00a39f7d63df1c092b63c12` and resolves that explicit first-party source in the same pip transaction as ReproSec. `SRIC_CORE_SOURCE=/path/to/sric-core` remains an explicit development/release-validation override.

The repair path preserves capsules, configuration and workspaces. It validates host Python and any existing venv; a stale/incomplete/broken environment rebuilds only the isolated ReproSec venv. It bootstraps `pip`, `setuptools` and `wheel`, runs `pip check`, imports `sric.web_console`, `sric.web_workbench`, `sric.web_catalog` and `sric.web_runtime`, requires SRIC `>=0.5.13,<0.6`, and smoke-tests doctor/capabilities plus all root help aliases before reporting success.

Installer-internal smokes use `SENTINEL_BANNER=never` and a temporary validation log. Successful installation therefore does not repeat the banner; failed smokes print captured diagnostics. Normal installation does not use `--force-reinstall`.

Termux prefers a writable `$PREFIX/bin` already present in `PATH`; standard Linux falls back to `~/.local/bin`. Windows uses SRIC's registry-backed `sric.install_path` helper rather than `setx` and accepts any Python 3 interpreter satisfying `>=3.11`.

## CLI presentation and help contract

Interactive terminals display `ReproSec Capsule :: v0.5.13`, `Developer: IsdarlinM`, then the purpose statement. Use `reprosec --no-color COMMAND`, `reprosec COMMAND --no-color`, or `NO_COLOR=1` for plain output.

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

- `/workbench` — the primary guided Security Console for every public `reprosec.cli_all` capability/parameter;
- `/console` — compatibility alias that opens the guided Security Console; it is not an argv-oriented user interface;
- `/api/v1/runtime-compatibility` — exact shared-runtime diagnostic.

The Workbench schema is generated from the installed CLI tree; parity coverage fails when a capability or parameter disappears from Web representation. Command metadata is normalized to JSON-safe primitives and enriched with choices, bounds and path semantics so the browser can choose appropriate controls without duplicating product logic. A catalog-construction failure returns a bounded/redacted HTTP 503 rather than an opaque HTTP 500.

Users do not type CLI command paths, option names, flags or free-form argv. Structured values are deterministically serialized only as an internal transport detail to the fixed runner. Execution uses `shell=False`, disabled stdin, CSRF protection, secret redaction, bounded/cancellable jobs, approval gates and SSE output. Timed-out child commands use bounded terminate/kill/wait handling plus background reaping if needed; recently pruned terminal jobs remain briefly available to active status/SSE readers. ReproSec's Scope, Policy, rate-limit, target validation and approval gates remain authoritative for capture/replay and all other active operations.

The native RCAP dashboard keeps real evidence actions such as Inspect, Redaction preview, Timeline and Verify; the Security Console complements those domain views instead of turning the dashboard into a terminal emulator.

## Updates and shared-runtime repair

```bash
reprosec update --check
reprosec update
reprosec update --force
```

Supported stale SRIC runtimes are advanced through immutable GitHub-signature-verified snapshots one release at a time from 0.5.5 through 0.5.13, avoiding unsafe rollback-metadata jumps. A same-version corrupt 0.5.13 runtime is repaired from the fixed verified 0.5.13 snapshot. No blind `git pull` fallback is used.

The ReproSec 0.5.13 official channel points to a GitHub-verified release commit and carries rollback metadata for the immediately preceding verified 0.5.12 snapshot.

## Validation gates

```bash
python -m sric.standalone_gate --root .
python scripts/release-gate.py
```

The 0.5.13 standalone regressions walk public ReproSec commands and help forms, exact ordered CLI/Web parameter parity, structured control types, absence of free-form argv UI, runtime compatibility and installer pinning. Existing suites cover native Web actions, local GET/POST APIs, RCAP parsers/importers, capture/replay, scope/DNS pinning, redaction, assertions, reports, fuzz/security and destructive-action gates.

`TEST_EVIDENCE.md` remains authoritative for actual execution. GitHub-hosted runners are currently blocked by an account billing lock; the affected workflows execute zero steps, are not PASS, and do not prove ReproSec's full exact-commit release gate. The current execution environment also lacks GitHub network/DNS access, so no substitute clone-based local full-suite PASS is claimed.

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
