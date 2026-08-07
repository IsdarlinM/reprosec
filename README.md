# ReproSec Capsule

```text
REPROSEC CAPSULE
imr :: v0.4.1
```

ReproSec is the reference implementation of `.rcap`: an open, deterministic container for portable and reproducible security evidence.

> **AI proposes. Evidence proves. Humans control.**

ReproSec never treats an LLM inference or a single unstable response as a confirmed vulnerability. Observations, workflows, assertions, provenance, repeated controls and replay evidence remain traceable to verifiable data.

## Implemented

- RCAP 0.3 actors, sessions, secret references, network/validation records and compatibility material for RCAP 0.1/0.2.
- Deterministic `.rcap` packing, SHA-256 manifests, Ed25519 signing and verification.
- Safe extraction with traversal, symlink, entry-count, decompression-size and compression-ratio controls.
- HAR, raw HTTP, constrained non-executing curl, Burp and ZAP imports.
- Structured redaction for headers, cookies, URL queries, JSON and form bodies, with preview before persistence.
- Explicit variables and ephemeral `--bind` values; unresolved values fail closed.
- Header, cookie, regex and JSON-path extractors.
- Extended assertions and privacy-preserving semantic JSON diff.
- Text and binary response evidence with full observed-body hash, size, retained-body limits and truncation state.
- Resolved IP, connected peer, HTTP version and TLS/ALPN network evidence where exposed by the transport.
- DNS-pinned direct replay preserving hostname, SNI and certificate verification.
- Environment proxies ignored by default; explicit proxy use requires acknowledgement.
- Gate order: `Scope -> Policy -> Rate Limit -> Approval -> Executor`.
- Redirects are opt-in and every destination is revalidated.
- Timeline, evidence lineage and observed actor/operation matrix; unobserved cells remain `UNKNOWN`.
- Authorized bounded HTTP capture, loopback proxy and browser-event recorder. CONNECT/TLS is metadata-only by default.
- Local FastAPI API and responsive Web UI.
- Offline synthetic demo requiring no API keys and making zero network requests.
- SRIC 0.4.1 workspaces, graph, lineage, notebook and evidence primitives.
- Multi-actor workflows, candidate workflow compiler, semantic differential v2 and public conformance fixtures.

## Replay stability in v0.4.1

Repeated responses can vary because of timestamps, tracing, request IDs, caches, A/B tests, transient errors or eventual consistency. ReproSec now provides deterministic stability analysis that:

- requires multiple samples;
- normalizes only explicitly approved volatile fields;
- computes canonical response fingerprints;
- reports volatile retained headers and JSON paths;
- calculates a flakiness score;
- prevents unstable sample sets from supporting `VALIDATED` findings.

See `docs/security/replay-stability.md`.

## Development install

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ../sric-core
python -m pip install -e '.[dev]'
python -m pytest
reprosec doctor
```

## Local release gate

No hosted CI service is required:

```bash
python scripts/release-gate.py
```

The gate runs static checks, tests, security scan, dependency audit, SBOM generation, package build, isolated wheel installation and CLI help smoke tests. Evidence is written to `build/release-evidence/release-gate.json`.

## First five minutes

```bash
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
reprosec import curl "curl -H 'Authorization: Bearer ...' https://api.example.com/me" --capsule case1
reprosec redact case1
reprosec redact case1 --apply
```

Imported commands and files are untrusted data and are never executed as instructions.

## Safe replay

```bash
reprosec replay case1 REQ-... --allow '*.example.com' --allow-method GET
```

An authorized mutating request additionally needs method scope and human approval:

```bash
reprosec replay case1 REQ-... --allow 'api.example.com' --allow-method POST --approve-action
```

## Security and privacy defaults

- Telemetry: **OFF**.
- Cloud AI: **OFF**.
- External uploads: **OFF**.
- Environment HTTP proxies: **ignored by replay**.
- Non-loopback Web/API exposure: **denied**.
- Imported content: **untrusted data, never instructions**.
- Required replay secrets: **ephemeral bindings or approved secret providers**.

## Known limits

Not yet claimed as complete: opt-in TLS interception with certificate lifecycle, full WebSocket/gRPC evidence capture, rich browser-state snapshots, complete Secret Vault replay bindings, long-running job orchestration for every operation, AI Reproduction Compiler, REP governance and authenticated non-loopback collaboration.

Use ReproSec only on systems you own or are explicitly authorized to test.
