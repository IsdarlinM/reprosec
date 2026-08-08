# RCAP 0.3

RCAP 0.3 is the current stable Reproducible Security Capsule format implemented by ReproSec 0.5.0.

## Design principles

- Evidence is immutable and integrity-addressed.
- AI output is advisory data and never validates a claim.
- Secrets are referenced, not embedded when avoidable.
- Historical/imported observations preserve provenance.
- Replay validation must be deterministic and scope/policy gated.

## Core records

RCAP 0.3 defines capsule metadata, actors, sessions, request/response records, workflow steps, assertions, extractors and validation records. A validation record may result in `VALIDATED`, `REJECTED` or `UNKNOWN`; `VALIDATED` requires deterministic assertions and evidence references at the application layer.

## Research context extension

ReproSec 0.5.0 adds a compatible research-context sidecar for Sentinel Forge investigations. It does not change the RCAP 0.3 capsule schema version. The sidecar may contain:

- `sentinel_case_id`
- an immutable `scope_snapshot`
- policy-decision records
- SRIC validation recipes
- tool provenance
- counter-evidence references

Mutating validation recipes require human approval. `OUT_OF_SCOPE` and `PROHIBITED` actions cannot be represented as executable validation recipes.

## Integrity

Capsule manifests use SHA-256 for file entries. Signatures cover deterministic capsule content according to the implementation's signing profile. Consumers must verify integrity before trusting replay evidence.

## Compatibility

Readers that only implement RCAP 0.3 may ignore the external research-context sidecar. Writers must not silently reinterpret older capsule truth states or discard provenance during migration.
