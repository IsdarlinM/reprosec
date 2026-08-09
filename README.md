# ReproSec Capsule

```text
ReproSec Capsule :: v0.5.3
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
- signed update flow with safe same-version `update --force` reinstall support;
- professional Rich/Typer terminal presentation with subdued green banner and `--no-color` support.

## Standalone install

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

SRIC Core is resolved automatically. `SRIC_CORE_SOURCE` is an explicit development/release-validation override only; installers never silently consume sibling repositories.

## CLI presentation

Interactive terminals display a compact subdued-green banner ordered as `ReproSec Capsule :: v0.5.3`, `Developer: IsdarlinM`, then the product purpose. Use `reprosec --no-color COMMAND`, `reprosec COMMAND --no-color`, or `NO_COLOR=1` for plain terminal presentation. The banner is emitted to interactive stderr so JSON, reports, exports and redirected stdout remain clean. See `docs/cli-presentation.md`.

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

ReproSec serves its responsive local application and API through `reprosec web`. It is **not an operating-system web shell**.

## Signed updates

The updater accepts only an Ed25519-signed manifest and a SHA-256 verified wheel. Configure `REPROSEC_RELEASE_MANIFEST_URL` plus `REPROSEC_RELEASE_PUBLIC_KEY`, or pass `--manifest` and `--public-key`.

```bash
reprosec update --check
reprosec update
reprosec update --force
```

`--force` reinstalls the selected signed release even when that exact version is already installed. It may install a newer signed version but never downgrades; `--check` and `--force` cannot be combined. No unsigned or blind `git pull` fallback is used. Until the official signed release channel is published, release-channel configuration remains explicit.

## Validation gates

```bash
python -m sric.standalone_gate --root .
python scripts/release-gate.py
```

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
