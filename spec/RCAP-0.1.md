# RCAP Draft Specification 0.1

An RCAP is a deterministic ZIP container. Paths are UTF-8 POSIX relative paths. The canonical reference layout includes `capsule.json`, `capsule.yaml`, `manifest.json`, `requests/`, `responses/`, `workflow/`, `assertions/`, `evidence/`, `redactions/`, `provenance/`, `signatures/`, and `reports/`.

`manifest.json` lists every non-signature file except itself, with SHA-256 and byte size. ZIP entries are written in lexical path order with a fixed DOS timestamp to support deterministic binary output.

Readers MUST reject absolute paths, parent traversal, symlinks, unreasonable entry counts, unreasonable uncompressed sizes, and suspicious compression ratios before extraction.

A signature, when present, signs the exact bytes of `manifest.json`. Draft 0.1 reference implementation uses Ed25519 local keys.

Truth states are: OBSERVED, INFERRED, HYPOTHESIS, VALIDATED, REJECTED, UNKNOWN. AI-generated structure MUST NOT be silently promoted to VALIDATED.
