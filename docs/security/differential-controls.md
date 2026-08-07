# Differential controls and passive protocol evidence

ReproSec 0.4.1 requires validation design to be separated from finding validation.

## Differential prerequisites

`assess_differential_design` checks:

- baseline and candidate samples;
- negative control by default;
- optional positive control;
- minimum repetition count;
- equivalent resource, state, session-age and environment contexts;
- deterministic stability evidence for every required role;
- explicit state reset after mutating samples.

A complete design returns `OBSERVED` readiness. It never returns `VALIDATED` and never confirms a vulnerability.

## Passive protocol records

WebSocket, gRPC and GraphQL records preserve bounded evidence metadata:

- connection and direction;
- frame/message/event ordering;
- payload hash, observed size, retained size and truncation state;
- protocol-specific metadata;
- evidence and provenance references;
- redaction state.

The protocol validator parses untrusted data only. It does not open sockets, replay messages, execute GraphQL operations or invoke gRPC methods.

CLI examples:

```bash
reprosec precision stability observations.json --policy stability-policy.json
reprosec precision differential-check samples.json stability.json
reprosec protocol validate records.json --kind websocket
```

API endpoints:

```text
POST /api/v1/precision/stability
POST /api/v1/precision/differential-check
POST /api/v1/protocol/validate
```
