# CLI Reference — reprosec

Generated from the registered runtime command tree. Every public command below supports `--help` and `-h`; top-level `COMMAND help` is normalized to the same help path.

## Commands

- `reprosec actor` — Manage explicit RCAP actors and sessions.
- `reprosec actor add` — Add an explicit actor without embedding credentials.
- `reprosec actor session` — Create an actor-scoped session containing only opaque secret references.
- `reprosec assertion` — Add a deterministic assertion.
- `reprosec browser` — Import sanitized browser-recorder events.
- `reprosec browser import` — Import sanitized navigation/HTTP/WebSocket/storage/DOM events from JSONL.
- `reprosec browser start` — Start a controlled browser-recorder lifecycle marker.
- `reprosec browser status` — Show recorder lifecycle state without exposing secrets.
- `reprosec browser stop` — Stop the controlled browser-recorder lifecycle marker.
- `reprosec capture` — Authorized/local evidence capture; capture never equals validation.
- `reprosec capture proxy` — Run loopback HTTP capture proxy. CONNECT records metadata only; no silent TLS MITM.
- `reprosec capture request` — Capture one authorized HTTP exchange through Scope/Policy/RateLimit/Approval.
- `reprosec capture tls-tunnel` — Record CONNECT/TLS tunnel metadata only.
- `reprosec check` — Evaluate one deterministic assertion against one stored response.
- `reprosec conformance` — Run RCAP layout, integrity and deterministic-pack conformance checks.
- `reprosec conformance-suite` — Run the public self-contained RCAP 0.3 conformance matrix.
- `reprosec demo` — Create an offline synthetic two-actor capsule.
- `reprosec diff` — Compare two responses without printing sensitive body content.
- `reprosec diff-v2` — Compare semantic/body/header/cookie/redirect/timing/network differences.
- `reprosec doctor` — Check runtime, dependencies, safe defaults and optional network prerequisites.
- `reprosec explain` — Show evidence lineage for a request.
- `reprosec extract` — Run a deterministic extractor.
- `reprosec help` — Show root or top-level command help.
- `reprosec import` — Import evidence without execution.
- `reprosec import burp` — Import a bounded Burp XML export as data.
- `reprosec import curl` — Parse curl as data; never execute it.
- `reprosec import har` — Import requests/responses from HAR.
- `reprosec import raw` — Import a raw HTTP request without executing it.
- `reprosec import zap` — Import bounded ZAP JSON/HAR as data.
- `reprosec init` — Create RCAP 0.3, optionally linked to shared SRIC workspace.
- `reprosec inspect` — Inspect capsule metadata and counts.
- `reprosec key` — Manage local Ed25519 signing keys.
- `reprosec matrix` — Build observed actor/operation matrix.
- `reprosec pack` — Create deterministic .rcap container and manifest.
- `reprosec query` — Search synchronized SRIC graph.
- `reprosec redact` — Preview/apply secret redaction.
- `reprosec replay` — Replay through Scope -> Policy -> Rate Limit -> Approval -> Executor.
- `reprosec report` — Export evidence/interpretation-separated report.
- `reprosec research-note` — Manage reproducible research notes.
- `reprosec sign` — Sign manifest with local Ed25519 key.
- `reprosec sync-lineage` — Index RCAP evidence into SRIC lineage/graph.
- `reprosec timeline` — Show deterministic evidence timeline.
- `reprosec update` — Check/install signed wheel release; never blind git pull.
- `reprosec validation-record` — Record deterministic validation evidence separately from capture/AI hypotheses.
- `reprosec verify` — Verify manifest hashes/signature.
- `reprosec version`
- `reprosec web` — Run local API/UI; non-loopback denied without authenticated TLS mode.
- `reprosec workflow` — Build deterministic multi-actor workflow steps.
- `reprosec workflow add` — Add workflow step.
- `reprosec workflow compile` — Compile candidate dependencies/extractors; replay required for proof.

## Help contract

```text
reprosec --help
reprosec -h
reprosec help
reprosec COMMAND --help
reprosec COMMAND -h
reprosec COMMAND help
```

Use command-specific help for authoritative arguments, options and defaults.
