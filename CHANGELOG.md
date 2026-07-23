# Changelog

## 0.4.0 - 2026-07-22
- Added RCAP 0.3 actors, sessions, secret references, network/validation records and backward-compatible conformance.
- Added bounded authorized capture, loopback HTTP proxy, browser recording lifecycle, multi-actor workflows and candidate workflow compilation.
- Added semantic differential v2, Burp/ZAP importers and public RCAP conformance fixtures.
- Upgraded shared integration to SRIC Core 0.4 workspaces, Claim-Evidence contracts, graph/jobs/lineage and secure defaults.
- Capture remains distinct from validation; CONNECT/TLS interception is never silently enabled.

## 0.3.0 - 2026-07-21
- Integrated RCAP evidence with SRIC 0.3 temporal graph, evidence lineage and reproducible research notebook primitives.
- Added `sync-lineage`, `research-note` and graph `query` commands without changing the RCAP 0.2 schema version.
- Updated runtime/tool version consistency across CLI, API, Web UI source and capsule metadata defaults.
- Retained deterministic replay, DNS pinning, scope/policy/rate/approval gates and RCAP 0.1/0.2 compatibility.

## 0.2.0 - 2026-07-21

### Security
- Added pre-connect DNS pinning using a dedicated network backend while preserving Host/SNI/certificate validation.
- Disabled implicit environment proxy routing for replay (`trust_env=False`); explicit proxy routing needs separate acknowledgement.
- Added structured query/JSON/form secret redaction and audit-target query redaction.
- Added conservative HTTP action classification; DELETE is destructive by default and GET/HEAD may be sensitive or mutating.
- Added streaming response size/retention limits, binary evidence handling and fail-closed unresolved variables.
- Redirect following is opt-in and each hop is revalidated.
- Added operational replay error codes and safe CLI error rendering.

### Evidence and reproduction
- Added RCAP Draft 0.2 schemas/specification, deterministic conformance checks and retained RCAP 0.1 schema material.
- Expanded safe curl parser for common real-world flags while keeping routing/TLS overrides inert metadata.
- Added ephemeral replay bindings and deterministic header/cookie/regex/JSONPath extractors.
- Added richer assertions, semantic JSON diff, timeline, evidence lineage and observed actor/operation matrix.
- Added response hashes, size/truncation metadata, binary base64 evidence and network observations.
- Added a gated single-interaction `capture` command and redacted audit trail.

### UI/API/quality
- Added functional workspace inspect, redaction-preview and timeline API/UI views.
- Added strict type checking for ReproSec.
- Expanded test coverage for SSRF/scope, DNS pinning, proxy policy, response limits, binary evidence, curl compatibility, extractors, conformance, matrix and help coverage.

## 0.1.0 - 2026-07-21
- Initial RCAP draft implementation.
- HAR/raw HTTP/constrained curl import with redaction.
- Deterministic pack/verify, safe extraction and Ed25519 signatures.
- Workflow steps, deterministic assertions, reports and offline demo.
- Policy/scope-gated replay with redirect and resolved-IP checks.
- Explicit redaction preview/apply and privacy-preserving response diff.
- Built React/Vite Web UI with functional integrity verification.
- Signed release update primitive inherited from SRIC.
- Local API, CLI help contract and test suites.
