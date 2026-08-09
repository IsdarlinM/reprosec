# ReproSec Capsule

```text
ReproSec Capsule :: v0.5.7
Developer: IsdarlinM

Capture, sanitize, replay, and package reproducible security evidence.
```

ReproSec is the reference implementation of `.rcap`: an open, deterministic container for portable and reproducible security evidence.

> **AI proposes. Evidence proves. Humans control.**

## Standalone by design

ReproSec is independently installable and independently useful. It depends on SRIC Core 0.5.x for common evidence/provenance/policy primitives, but AuthTwin, FossilScope, TrustBoundary Mapper and Exposure DNA are never required for capture, import, replay, validation, reporting, CLI, API or Web UI.

```bash
reprosec doctor
reprosec capabilities
```

Compatible Sentinel Forge products add optional research capabilities through shared contracts and RCAP evidence; they are not runtime prerequisites.

## Implemented

- RCAP 0.3 actors, sessions, secret references, network/validation records and compatibility material for RCAP 0.1/0.2;
- deterministic `.rcap` packing, SHA-256 manifests, Ed25519 signing and verification;
- safe extraction with traversal, symlink, entry-count, decompression-size and compression-ratio controls;
- HAR, raw HTTP, constrained non-executing curl, Burp and ZAP imports;
- structured redaction with preview before persistence;
- explicit variables and ephemeral bindings; unresolved values fail closed;
- response evidence with hashes, size, truncation state and retained-body limits;
- DNS-pinned direct replay preserving hostname, SNI and certificate verification;
- gate order `Scope -> Policy -> Rate Limit -> Approval -> Executor`;
- redirects are opt-in and every destination is revalidated;
- timeline, evidence lineage and observed actor/operation matrix;
- authorized bounded HTTP capture, loopback proxy and browser-event recorder; CONNECT/TLS is metadata-only by default;
- evidence-native research context linking scope snapshots, policy decisions, validation recipes, tool provenance and counter-evidence;
- local FastAPI API, responsive Web UI and offline synthetic demo;
- SRIC 0.5.x workspaces, graph, lineage, notebook and evidence primitives;
- zero-config official update flow with same-version `update --force`, rollback and first-party runtime repair;
- exact SRIC version/module compatibility checks in `doctor` and the local API;
- full Web Feature Workbench with every public ReproSec CLI command and argument represented as structured responsive controls;
- degraded Web mode that preserves the native dashboard and returns an actionable 503 for an unavailable shared Workbench instead of crashing the entire CLI;
- advanced Web Command Console with exact public CLI command-tree parity and real-time jobs;
- professional Rich/Typer terminal presentation with subdued green banner and `--no-color` support.

## Standalone install and repair

Linux:

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

SRIC Core is resolved automatically. `SRIC_CORE_SOURCE` is an explicit development/release-validation override only; installers never silently consume sibling repositories. The installers are also repair-capable: they force-reinstall the pinned first-party runtime and product, run `pip check`, verify `sric.web_console` and `sric.web_workbench`, and only then run doctor/capability/help smokes. Existing capsules, configuration and workspaces are not deleted by this repair path.

## CLI presentation

Interactive terminals display a compact subdued-green banner ordered as `ReproSec Capsule :: v0.5.7`, `Developer: IsdarlinM`, then the product purpose. Use `reprosec --no-color COMMAND`, `reprosec COMMAND --no-color`, or `NO_COLOR=1` for plain terminal presentation. The banner is emitted to interactive stderr so JSON, reports, exports and redirected stdout remain clean.

The help contract covers `reprosec --help`, `reprosec -h`, `reprosec help`, `reprosec COMMAND --help`, `reprosec COMMAND -h` and `reprosec COMMAND help`.

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

Imported commands and files are untrusted data and are never executed as instructions.

## Safe replay

```bash
reprosec replay case1 REQ-... --allow '*.example.com' --allow-method GET
```

Authorized mutating requests additionally require method scope and human approval.

## Web and API

`reprosec web` serves the native evidence dashboard plus two shared SRIC surfaces:

- `/workbench` — **All Features**: every public `reprosec.cli_all` command and every CLI parameter rendered as a structured Web form;
- `/console` — advanced argv-oriented command console;
- `/api/v1/runtime-compatibility` — exact shared-runtime diagnostic.

The Workbench generates its feature schema from the installed CLI tree; the release gate fails if a command or parameter disappears from Web representation. If an installed SRIC is stale/corrupt, shared Web modules are loaded lazily: the CLI and native dashboard remain reachable and `/workbench` reports `RUNTIME_INCOMPATIBLE` with repair guidance instead of causing a module-import traceback.

Neither shared surface is an operating-system shell. Execution uses the fixed SRIC runner with `shell=False`, disabled stdin, CSRF protection, secret redaction, bounded/cancellable jobs and SSE output. ReproSec's Scope, Policy, rate-limit, target-validation and approval gates remain authoritative for capture/replay and other active operations.

## Updates

The official update path is zero-config:

```bash
reprosec update --check
reprosec update
reprosec update --force
```

Before an official product update, ReproSec now verifies the shared SRIC version and required modules. Supported stale 0.5.x runtimes are repaired through immutable, GitHub-signature-verified historical snapshots and the official channel; a same-version runtime missing required modules is force-reinstalled. Custom/private `--manifest` plus `--public-key` updates remain explicit and do not silently switch the core to an official channel.

Normal users do **not** provide a manifest or public key. The official updater accepts only fixed Sentinel Forge repositories, validates immutable signed commits and source metadata, backs up state, installs without a shell and verifies the installed distribution. `--force` can reinstall the current official release or move forward, never downgrade. No blind `git pull` fallback is used.

## Validation gates

```bash
python -m sric.standalone_gate --root .
python scripts/release-gate.py
```

The 0.5.7 interface/runtime regression suite reproduces stale-SRIC and missing-Workbench states, checks signed transition/repair behavior, validates degraded Web 503 behavior, walks every public ReproSec command with both help flags and trailing-help normalization, and compares every ordered CLI parameter with the Web Feature Workbench schema. Existing unit/integration/E2E/security/fuzz suites remain authoritative for RCAP, import, replay, scope, DNS pinning, redaction, assertions, reporting and other business features. Destructive operations are gate-tested rather than executed solely for coverage.

Standalone and release evidence are written below `build/release-evidence/`. A release requires PASS tied to the exact commit/tree.

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
