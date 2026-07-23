# Roadmap

## Current — 0.4.x hardening
Implemented: RCAP 0.3 actors/sessions/validation records, authorized bounded HTTP capture, loopback proxy with CONNECT metadata-only behavior, browser recording lifecycle, multi-actor workflows, workflow compiler, semantic differential v2, Burp/ZAP imports, public conformance suite and SRIC 0.4 shared-workspace integration.

Next:
- Explicit opt-in TLS interception adapter with certificate lifecycle and strict authorization controls; never silent MITM.
- WebSocket/gRPC evidence records and richer GraphQL workflow semantics.
- Secret Vault bindings from SRIC for actor/session replay without embedding secrets in RCAP.
- Long-running import/replay jobs over SRIC Job Engine v2 with resumability and SSE progress.
- REP governance, larger public conformance corpus and third-party implementation compatibility testing.

## 1.0
Stable RCAP schema/governance, migration compatibility, signed releases, external implementations/conformance and audited replay security model.
