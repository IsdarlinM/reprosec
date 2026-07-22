# ReproSec Capsule

```text
REPROSEC CAPSULE
imr :: v0.3.0
```

ReproSec is the reference implementation of `.rcap`: an open, deterministic container for portable and reproducible security evidence.

> **AI proposes. Evidence proves. Humans control.**

ReproSec does not treat an LLM inference as a confirmed vulnerability. It preserves observations, workflows, assertions, provenance and replay evidence so that humans can validate conclusions deterministically.

## v0.3 capabilities

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
- Single-interaction authorized `capture` command using the same safety gates.
- FastAPI local API and dependency-light static Web UI with functional integrity, workspace inspection, redaction preview and timeline views.
- Signed release update primitive; no blind production `git pull`.
- Offline synthetic demo requiring no API keys and making zero network requests.
- SRIC 0.3 evidence-lineage/graph synchronization (`sync-lineage`), reproducible research notes and shared graph queries.
- RCAP schema version remains independently versioned at Draft 0.2; tool upgrades do not silently rewrite historical evidence formats.

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

Read-only request:

```bash
reprosec replay case1 REQ-... \
  --allow '*.example.com' \
  --allow-method GET
```

An authorized mutating request needs both method scope and human approval:

```bash
reprosec replay case1 REQ-... \
  --allow 'api.example.com' \
  --allow-method POST \
  --approve-action
```

Bind a redacted value only in memory:

```bash
reprosec replay case1 REQ-... \
  --allow 'api.example.com' \
  --bind REDACTED_AUTHORIZATION_1='Bearer ...'
```

Loopback/private networks remain blocked unless explicitly allowed for an authorized lab:

```bash
reprosec replay case1 REQ-... \
  --allow 127.0.0.1 \
  --allow-network 127.0.0.0/8
```

Redirects are not followed unless `--follow-redirects` is provided. Every followed destination is re-evaluated through scope and DNS/network policy.

## Capture one authorized interaction

```bash
reprosec capture case1 https://example.com/health \
  --allow example.com \
  --allow-method GET
```

This is a gated direct HTTP capture, **not yet a browser/MITM proxy capture engine**.

## Deterministic extractors

```bash
reprosec extract case1 RES-... DOCUMENT_ID jsonpath '$.document.id'
reprosec extract case1 RES-... SESSION cookie session --sensitive
```

Sensitive extracted values are not printed unless explicitly requested with `--reveal`.

## Semantic diff and assertions

```bash
reprosec diff case1 RES-EXPECTED RES-OBSERVED --semantic
reprosec assertion case1 REQ-... jsonpath_equals A --selector '$.actor.id'
reprosec check case1 AST-... RES-...
```

Semantic diff reports paths and change types without echoing changed JSON values.

## Network diagnostics

```bash
reprosec doctor --network
```

The network diagnostic checks DNS prerequisites and reports proxy environment presence without sending an HTTP request to a target.

## Web UI

```bash
reprosec web
```

The v0.3 UI is local-loopback only. Non-loopback binding remains denied until authenticated TLS mode is implemented.

## Security and privacy defaults

- Telemetry: **OFF**.
- Cloud AI: **OFF**.
- External uploads: **OFF**.
- Environment HTTP proxies: **ignored by replay**.
- Non-loopback Web/API exposure: **denied**.
- Imported content: **untrusted data, never instructions**.
- Required replay secrets: **explicit ephemeral bindings or future approved secret providers; never silently omitted**.

See `SECURITY.md`, `PRIVACY.md`, `docs/security/threat-model.md`, `spec/RCAP-0.2.md` and `IMPLEMENTATION_STATUS.md` in the foundation bundle for exact boundaries.

## Known v0.3 limits

Not yet claimed as complete: full browser/MITM capture, Burp/ZAP adapters, WebSocket/GraphQL/gRPC records, browser-state snapshots, full CLI/Web parity, secure vault/keyring integration, job/SSE streaming, AI Reproduction Compiler, full REP governance, authenticated non-loopback collaboration and official embedded release trust roots.

## Ethics

Use ReproSec only on systems you own or are explicitly authorized to test. Keep targets in scope, minimize data, avoid disruption, and preserve evidence/provenance for every conclusion.
