from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

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


def _semver_parts(value: str) -> tuple[tuple[int, int, int], tuple[str, ...] | None]:
    precedence = value.split("+", 1)[0]
    core, separator, prerelease = precedence.partition("-")
    major, minor, patch = core.split(".")
    return (int(major), int(minor), int(patch)), tuple(prerelease.split(".")) if separator else None


def _compare_semver(left: str, right: str) -> int:
    left_core, left_pre = _semver_parts(left)
    right_core, right_pre = _semver_parts(right)
    if left_core != right_core:
        return 1 if left_core > right_core else -1
    if left_pre is None and right_pre is None:
        return 0
    if left_pre is None:
        return 1
    if right_pre is None:
        return -1
    for left_id, right_id in zip(left_pre, right_pre):
        if left_id == right_id:
            continue
        left_numeric, right_numeric = left_id.isdigit(), right_id.isdigit()
        if left_numeric and right_numeric:
            return 1 if int(left_id) > int(right_id) else -1
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return 1 if left_id > right_id else -1
    if len(left_pre) == len(right_pre):
        return 0
    return 1 if len(left_pre) > len(right_pre) else -1


def _find_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _updater() -> ModuleType:
    try:
        return importlib.import_module("sric.updater")
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError("SRIC updater is unavailable; rerun the product installer") from exc


def status() -> SRICRuntimeStatus:
    reasons: list[str] = []
    try:
        version = importlib.metadata.version("sric-core")
    except importlib.metadata.PackageNotFoundError:
        version = None
        reasons.append("sric-core is not installed")
    if version is not None:
        try:
            if _compare_semver(version, SRIC_MIN_FULL) < 0:
                reasons.append(f"sric-core {version} is older than required {SRIC_MIN_FULL}")
            if _compare_semver(version, SRIC_MAX_EXCLUSIVE) >= 0:
                reasons.append(f"sric-core {version} is outside supported range <{SRIC_MAX_EXCLUSIVE}")
        except (TypeError, ValueError):
            reasons.append(f"sric-core has an unsupported version string: {version}")
    missing = tuple(name for name in SRIC_REQUIRED_MODULES if not _find_module(name))
    if missing:
        reasons.append("missing shared modules: " + ", ".join(missing))
    return SRICRuntimeStatus(version, not reasons, missing, tuple(reasons))


def _require_updater_api(updater: ModuleType, *names: str) -> None:
    missing = [name for name in names if not callable(getattr(updater, name, None))]
    if missing:
        raise RuntimeError(
            "installed SRIC updater is too old for safe in-place bootstrap (missing "
            + ", ".join(missing)
            + "); rerun the product installer"
        )


def _upgrade_055_to_056() -> None:
    """Bridge 0.5.5 to 0.5.6 using immutable, signature-verified history."""
    updater = _updater()
    _require_updater_api(
        updater,
        "_download_official_archive",
        "install_verified_package",
        "_verify_installed_distribution",
    )
    with tempfile.TemporaryDirectory(prefix="sentinel-sric-bootstrap-") as td:
        root = Path(td)
        target = updater._download_official_archive(
            repository=SRIC_REPOSITORY,
            commit=SRIC_056_COMMIT,
            expected_product="sric-core",
            expected_version="0.5.6",
            destination=root / "sric-core-0.5.6.zip",
        )
        rollback = updater._download_official_archive(
            repository=SRIC_REPOSITORY,
            commit=SRIC_055_COMMIT,
            expected_product="sric-core",
            expected_version="0.5.5",
            destination=root / "sric-core-0.5.5.zip",
        )
        try:
            updater.install_verified_package(target, force_reinstall=True)
            updater._verify_installed_distribution("sric-core", "0.5.6")
        except Exception:
            updater.install_verified_package(rollback, force_reinstall=True)
            updater._verify_installed_distribution("sric-core", "0.5.5")
            raise
    importlib.invalidate_caches()


def ensure_for_official_update() -> SRICRuntimeStatus:
    current = status()
    if current.compatible:
        return current
    if current.version is None:
        raise RuntimeError("sric-core is missing; rerun the product installer")
    try:
        if _compare_semver(current.version, SRIC_MAX_EXCLUSIVE) >= 0:
            raise RuntimeError("installed sric-core is newer than this product supports")
        if _compare_semver(current.version, "0.5.5") < 0:
            raise RuntimeError("sric-core is too old for in-place bootstrap; rerun the product installer")
    except ValueError as exc:
        raise RuntimeError("installed sric-core version cannot be safely compared") from exc

    working_version = current.version
    if working_version == "0.5.5":
        _upgrade_055_to_056()
        working_version = "0.5.6"

    updater = _updater()
    _require_updater_api(updater, "perform_product_update")
    force = _compare_semver(working_version, SRIC_MIN_FULL) >= 0
    updater.perform_product_update(
        expected_product="sric-core",
        current_version=working_version,
        check_only=False,
        force=force,
    )
    importlib.invalidate_caches()
    repaired = status()
    if not repaired.compatible:
        raise RuntimeError(
            "SRIC repair finished but compatibility is still invalid: "
            + "; ".join(repaired.reasons)
        )
    return repaired
