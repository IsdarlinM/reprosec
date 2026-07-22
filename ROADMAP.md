# Roadmap

## Current — 0.3.x hardening
RCAP 0.2 compatibility, safe replay with DNS pinning/scope-policy-rate-approval gates, structured redaction, variables/extractors, assertions, semantic diff, binary/streaming evidence, SRIC lineage/notebook/query integration and conformance checks are implemented.

Next:
- Full scoped browser/proxy capture engine with explicit certificate lifecycle.
- Burp/ZAP import adapters, WebSocket/GraphQL/gRPC evidence records and sanitized browser-state snapshots.
- Keyring/vault-backed secret bindings and job/SSE integration for long replays/imports.
- Expanded parser fuzzing/curl compatibility and richer public RCAP conformance suite/REP governance.
- Optional AI Reproduction Compiler that only emits candidate workflows and never validates findings.

## 1.0
Stable RCAP schema/governance, migration compatibility, signed releases, external implementations/conformance and audited replay security model.
