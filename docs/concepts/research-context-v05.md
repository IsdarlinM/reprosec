# Research Context in ReproSec 0.5

ReproSec 0.5 keeps RCAP 0.3 as the stable capsule format and adds an optional evidence-native research context for Sentinel Forge investigations.

The context can reference a Sentinel Case, an immutable scope snapshot, policy decisions, SRIC validation recipes, tool provenance, counter-evidence and additional non-secret metadata.

Research context never validates a finding. It records why a deterministic replay or assertion was proposed and which safety decisions governed it.

## Safety

`OUT_OF_SCOPE` and `PROHIBITED` actions cannot be represented by SRIC validation recipes. Mutating recipes require human approval. A destructive policy decision also requires a recorded approver.

Secrets should be referenced through the shared secret/vault layer rather than copied into capsules or logs.

## Integrity

`CapsuleResearchContext.sha256()` produces a deterministic digest of the normalized context. It is intended for evidence packaging, comparison and provenance checks; it is not a substitute for RCAP manifest/signature verification.
