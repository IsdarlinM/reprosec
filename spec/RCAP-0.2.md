# RCAP Draft Specification 0.2

RCAP 0.2 is an open, deterministic container for portable security evidence. It remains a draft and does not claim standards status.

## Container

An `.rcap` is a deterministic ZIP with UTF-8 POSIX relative paths. The reference layout is:

```text
capsule.json
capsule.yaml
manifest.json
actors/
environment/
workflow/
requests/
responses/
evidence/
assertions/
extractors/
timeline/
redactions/
provenance/
signatures/
reports/
```

Readers MUST reject absolute paths, parent traversal, symlinks, excessive entry counts, excessive uncompressed size and suspicious compression ratios before extraction.

## Integrity

`manifest.json` lists each non-signature file except itself with SHA-256 and byte size. ZIP entries use lexical path ordering and canonical timestamps in the reference implementation. Signatures cover the exact manifest bytes. Ed25519 is the reference local signing mechanism.

## Truth and evidence

Allowed truth states are `OBSERVED`, `INFERRED`, `HYPOTHESIS`, `VALIDATED`, `REJECTED`, and `UNKNOWN`. AI output MUST NOT be promoted to `VALIDATED` without deterministic evidence.

## HTTP evidence fidelity

Request and response records may carry duplicate ordered headers, text or base64-encoded binary bodies, raw-body SHA-256 and byte size, truncation state, media type, resolved destination IPs, connected peer IP, HTTP/TLS version and ALPN when observable, peer verification state, and explicit proxy metadata.

## Redaction and variables

Sensitive values SHOULD be replaced by explicit variables such as `${{REDACTED_ACCESS_TOKEN_1}}`. Redaction MUST cover, when structurally recognizable, headers, cookies, query parameters, JSON and form-urlencoded data. Implementations MUST NOT silently drop a required secret during deterministic replay.

## Extractors

Deterministic extractors MAY derive variables from stored responses. Draft 0.2 defines reference kinds: `header`, `cookie`, `regex`, and simple JSONPath-like dot paths. Extractor outputs are evidence-derived values, not security conclusions.

## Replay safety

Active replay MUST pass through scope, policy, rate limits and approval before execution. Direct HTTP replay SHOULD pin connections to scope-validated DNS results while retaining the original hostname for `Host`, SNI and certificate validation. Redirects, when enabled, MUST be revalidated on every hop. Environment proxy variables MUST NOT silently change routing.

## Compatibility

The v0.2 reference implementation keeps the v0.1 schema file under `schemas/0.1/`. Schema migration remains explicit; historical evidence MUST NOT be silently rewritten.
