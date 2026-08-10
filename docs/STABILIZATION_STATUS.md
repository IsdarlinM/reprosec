# ReproSec Capsule 0.5.13 stabilization status

Date: 2026-08-10

ReproSec 0.5.13 is under Sentinel Forge P0/P1 stabilization and must not be described as a fully gated stable release until the exact release commit passes the coordinated gates.

Current blockers include hosted GitHub Actions allocating zero runners, the ecosystem dependency advisory review, signed release/SBOM/provenance requirements, and full Windows/Linux Python 3.11-3.13 validation.

This stabilization branch fixes the audited FastAPI application-construction blocker, adds a data-preserving Windows uninstaller and removes the CI dependency on private tokens/branch-name coupling. The official update channel is intentionally unchanged until those gates execute.
