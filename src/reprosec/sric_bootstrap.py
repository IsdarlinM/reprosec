from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sric.updater import (
    _compare_semver,
    _download_official_archive,
    _verify_installed_distribution,
    install_verified_package,
    perform_product_update,
)

SRIC_MIN_FULL = "0.5.7"
SRIC_MAX_EXCLUSIVE = "0.6.0"
SRIC_REQUIRED_MODULES = ("sric.web_console", "sric.web_workbench")
SRIC_REPOSITORY = "IsdarlinM/sric-core"
SRIC_055_COMMIT = "6217b4e0b8b1a7b69f2f64181d1e3b22fd4bc221"
SRIC_056_COMMIT = "8858854e22a6d1154e676c4cb6684b87d610d36f"


@dataclass(frozen=True)
class SRICRuntimeStatus:
    version: str | None
    compatible: bool
    missing_modules: tuple[str, ...]
    reasons: tuple[str, ...]


def _find_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def status() -> SRICRuntimeStatus:
    reasons: list[str] = []
    try:
        version = importlib.metadata.version("sric-core")
    except importlib.metadata.PackageNotFoundError:
        version = None
        reasons.append("sric-core is not installed")
    if version is not None:
        if _compare_semver(version, SRIC_MIN_FULL) < 0:
            reasons.append(f"sric-core {version} is older than required {SRIC_MIN_FULL}")
        if _compare_semver(version, SRIC_MAX_EXCLUSIVE) >= 0:
            reasons.append(f"sric-core {version} is outside supported range <{SRIC_MAX_EXCLUSIVE}")
    missing = tuple(name for name in SRIC_REQUIRED_MODULES if not _find_module(name))
    if missing:
        reasons.append("missing shared modules: " + ", ".join(missing))
    return SRICRuntimeStatus(version, not reasons, missing, tuple(reasons))


def _upgrade_055_to_056() -> None:
    """Bridge the last pre-Workbench official core using fixed signed commits.

    This code intentionally uses only updater primitives already present in SRIC
    0.5.5, because importing a newer SRIC helper is exactly what a stale runtime
    cannot do. Both source archives are verified against GitHub commit signatures
    before pip receives them, and rollback is attempted on failure.
    """

    with tempfile.TemporaryDirectory(prefix="sentinel-sric-bootstrap-") as td:
        root = Path(td)
        target = _download_official_archive(
            repository=SRIC_REPOSITORY,
            commit=SRIC_056_COMMIT,
            expected_product="sric-core",
            expected_version="0.5.6",
            destination=root / "sric-core-0.5.6.zip",
        )
        rollback = _download_official_archive(
            repository=SRIC_REPOSITORY,
            commit=SRIC_055_COMMIT,
            expected_product="sric-core",
            expected_version="0.5.5",
            destination=root / "sric-core-0.5.5.zip",
        )
        try:
            install_verified_package(target, force_reinstall=True)
            _verify_installed_distribution("sric-core", "0.5.6")
        except Exception:
            install_verified_package(rollback, force_reinstall=True)
            _verify_installed_distribution("sric-core", "0.5.5")
            raise
    importlib.invalidate_caches()


def ensure_for_official_update() -> SRICRuntimeStatus:
    current = status()
    if current.compatible:
        return current
    if current.version is None:
        raise RuntimeError("sric-core is missing; rerun the product installer")
    if _compare_semver(current.version, SRIC_MAX_EXCLUSIVE) >= 0:
        raise RuntimeError("installed sric-core is newer than this product supports")
    if _compare_semver(current.version, "0.5.5") < 0:
        raise RuntimeError("sric-core is too old for in-place bootstrap; rerun the product installer")

    working_version = current.version
    if working_version == "0.5.5":
        _upgrade_055_to_056()
        working_version = "0.5.6"

    force = _compare_semver(working_version, SRIC_MIN_FULL) >= 0
    perform_product_update(
        expected_product="sric-core",
        current_version=working_version,
        check_only=False,
        force=force,
    )
    importlib.invalidate_caches()
    repaired = status()
    if not repaired.compatible:
        raise RuntimeError("SRIC repair finished but compatibility is still invalid: " + "; ".join(repaired.reasons))
    return repaired
