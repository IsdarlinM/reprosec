# ReproSec Capsule

```text
REPROSEC CAPSULE
imr :: v0.4.0
```

ReproSec is the reference implementation of `.rcap`: an open, deterministic container for portable and reproducible security evidence.

> **AI proposes. Evidence proves. Humans control.**

ReproSec does not treat an LLM inference as a confirmed vulnerability. It preserves observations, workflows, assertions, provenance and replay evidence so a conclusion can be traced back to verifiable data.

## What v0.4.0 implements

- RCAP 0.3 with actors, sessions, secret references, network/validation records, plus retained compatibility material for RCAP 0.1/0.2.
- Deterministic `.rcap` packing, SHA-256 manifests, Ed25519 signing and verification.
- Safe archive extraction with traversal, symlink, entry-count, decompression-size and compression-ratio controls.
- HAR, raw HTTP and expanded non-executing `curl` import.
- Structured secret redaction for headers/cookies, URL query parameters, JSON and form-urlencoded bodies.
- Redaction preview before persistence.
- Explicit variables: unresolved `${{NAME}}` values fail closed during replay and can be bound ephemerally with `--bind`.
- Deterministic extractors: header, cookie, regex and simple JSONPath-like dot paths.
- Extended assertions and privacy-preserving semantic JSON diff.
- Text and binary response evidence, full observed-body hash/size, bounded retained body and truncation state.
- Network evidence: resolved IPs, connected peer, HTTP version and TLS/ALPN when exposed by the transport.
- Direct replay DNS pinning: TCP connects only to the already scope-validated IP set while preserving hostname/SNI/certificate verification.
- Environment proxies ignored by default (`trust_env=False`). Explicit proxy routing requires separate acknowledgement.
- Gate order: `Scope -> Policy -> Rate Limit -> Approval -> Executor`.
- GET/HEAD are not blindly classified as safe; sensitive/mutating path semantics and DELETE are conservatively classified.
- Redirect following is opt-in and every hop is revalidated.
- Streaming download/storage limits to reduce oversized-response and decompression-risk exposure.
- Operational replay error codes instead of raw tracebacks by default.
- Read-only timeline, evidence lineage (`explain`) and observed actor/operation matrix (`UNKNOWN` is never treated as a vulnerability).
- RCAP conformance checks for layout, integrity and deterministic packing.
- Local audit trail in `provenance/audit.jsonl`, with target secret redaction.
- Authorized bounded HTTP capture, loopback capture proxy and browser-event recorder using the same safety gates; CONNECT/TLS is recorded as tunnel metadata and is not silently MITM-intercepted.
- FastAPI local API and dependency-light responsive Web UI with integrity, workspace inspection, redaction preview, timeline and runtime capability views.
- Signed release update primitive; no blind production `git pull`.
- Offline synthetic demo requiring no API keys and making zero network requests.
- SRIC 0.4 evidence-lineage/graph synchronization (`sync-lineage`), reproducible research notes and shared graph queries.
- RCAP remains independently versioned at 0.3; tool upgrades do not silently rewrite historical evidence formats.
- Multi-actor/session workflows, candidate workflow compiler, semantic differential v2, Burp/ZAP imports and a public conformance suite are implemented.
- Capsules can link to a shared SRIC 0.4 workspace by opaque `workspace_id` without embedding workspace secrets.

## Install for development

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ../sric-core
python -m pip install -e '.[dev]'
pytest
reprosec doctor
```

Linux and Windows installer scripts are available under `scripts/`. Generated binaries and virtual environments are not stored in the repository.

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

The demo performs **zero network requests**.

## Import evidence

```bash
reprosec init case1 --title "Authorized test case"
reprosec import har session.har --capsule case1
reprosec import raw request.txt --capsule case1
reprosec import curl "curl -L --max-time 10 -H 'Authorization: Bearer ...' https://api.example.com/me" --capsule case1
reprosec redact case1
reprosec redact case1 --apply
```

Imported curl commands are parsed as untrusted data and are **never executed**. Network-routing/TLS overrides such as `--resolve`, `--connect-to`, proxies or `-k` are represented as metadata rather than silently applied.

## Safe replay

```bash
reprosec replay case1 REQ-... --allow '*.example.com' --allow-method GET
```

An authorized mutating request needs both method scope and human approval:

```bash
reprosec replay case1 REQ-... --allow 'api.example.com' --allow-method POST --approve-action
```

Bind a redacted value only in memory with `--bind`; loopback/private networks remain blocked unless explicitly allowlisted for an authorized lab. Redirects are opt-in and every followed destination is re-evaluated through scope and DNS/network policy.

## Capture authorized evidence

```bash
reprosec capture request case1 GET https://example.com/health --allow example.com
```

ReproSec v0.4 also provides a loopback HTTP capture proxy and controlled browser-event recorder. CONNECT/TLS is metadata-only by default; silent MITM is never enabled. Capture remains evidence acquisition, not validation.

## Web UI

```bash
reprosec web
```

The v0.4 UI is local-loopback only. Non-loopback binding remains denied until authenticated TLS mode is implemented.

## Security and privacy defaults

- Telemetry: **OFF**.
- Cloud AI: **OFF**.
- External uploads: **OFF**.
- Environment HTTP proxies: **ignored by replay**.
- Non-loopback Web/API exposure: **denied**.
- Imported content: **untrusted data, never instructions**.
- Required replay secrets: **explicit ephemeral bindings or approved secret providers; never silently omitted**.

## Known v0.4 limits

Not yet claimed as complete: opt-in TLS interception with certificate lifecycle, full WebSocket/gRPC evidence capture, rich browser-state snapshots, complete SRIC Secret Vault replay bindings, long-running job/SSE orchestration for all operations, AI Reproduction Compiler, full REP governance, authenticated non-loopback collaboration and official embedded release trust roots.

## Ethics

Use ReproSec only on systems you own or are explicitly authorized to test. Keep targets in scope, minimize data, avoid disruption, and preserve evidence/provenance for every conclusion.
