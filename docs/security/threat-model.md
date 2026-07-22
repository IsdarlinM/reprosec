# Threat Model v0.2

## Assets
Capsules, raw evidence, scope policy, signing keys, reports and replay credentials.

## Threats / controls
- Malicious archives: safe extraction limits, no symlinks, no traversal.
- SSRF / redirects / DNS changes: evaluate resolved destination and every redirect through scope controls.
- Secret leakage: import-time redaction and no cloud uploads by default.
- Prompt injection: no autonomous AI processing in v0.2; future AI receives labeled untrusted data and remains outside policy enforcement.
- Replay misuse: explicit allowlist and enforced Scope -> Policy -> Rate Limit -> Approval -> Executor path; mutations need approval; prohibited actions remain denied by SRIC policy.
- Signature confusion: signs exact manifest bytes; manifest excludes signature files to avoid cycles.
