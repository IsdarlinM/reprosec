# Changelog

## 0.5.2 - 2026-08-08
- Added a subdued green interactive CLI banner with product description and `IsdarlinM :: v0.5.2` signature.
- Added colorized Typer/Rich command help plus global `--no-color` and `NO_COLOR` support.
- Kept banner output on interactive stderr so JSON, exports and automation stdout remain clean.
- Added CLI branding regression tests and documentation.
- Updated the SRIC Core runtime floor, lock and first-party source pin to 0.5.2.

## 0.5.1 - 2026-08-08
- Fixed clean installation when `sric-core` is not published on PyPI.
- Added a first-party dependency manifest pinned to the exact SRIC Core 0.5.1 GitHub commit.
- Windows and Linux installers now bootstrap Sentinel Forge first-party dependencies before installing ReproSec and its third-party runtime closure.
- Preserved `SRIC_CORE_SOURCE` as an explicit development/release-validation override.
- Updated the runtime lock and package dependency floor to SRIC Core 0.5.1.
- Added standalone regression coverage for the installer dependency contract.

## 0.5.0 - 2026-08-08
- Added evidence-native RCAP research context linking capsules to Sentinel Cases without changing RCAP 0.3 compatibility.
- Added immutable scope snapshots, policy-decision records, validation recipes, tool provenance and counter-evidence references.
- Added safety validation for destructive policy decisions and cross-reference integrity between recipes and policy decisions.
- Added deterministic SHA-256 research-context fingerprints for evidence packaging and comparison.
- Published the missing RCAP 0.3 specification and aligned the current schema pointer with the runtime RCAP 0.3 contract.
- Updated runtime metadata and the SRIC dependency contract for the Sentinel Forge 0.5 release train.
- Added standalone capability discovery with no mandatory sibling-product dependencies.
- Reworked Linux/Windows installers so SRIC 0.5 is resolved as a package dependency; sibling repositories are no longer auto-detected.
- Added standalone CLI/API/Web tests, recursive help/parser contracts, clean-install smokes and data-preserving Linux uninstall behavior.
- Added 0.5 regression tests for research-context integrity and safety gates.

## 0.4.1 - 2026-08-06
- Added deterministic replay stability analysis across repeated observations.
- Added explicit normalization policies for volatile headers, JSON paths and regex-defined dynamic values.
- Added response fingerprints, dominant-sample measurement, flakiness scoring and retained volatile-field reporting.
- Unstable sample sets now explicitly state that assertions must not create `VALIDATED` findings.
- Added regression tests for request IDs, timestamps, dynamic JSON, status-code variation, regex normalization and minimum sample counts.
- Replaced hosted GitHub Actions/Dependabot automation with the cross-platform local Sentinel Forge release gate.
- Updated the SRIC dependency floor to 0.4.1 and added local build/dependency-audit tooling.

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
