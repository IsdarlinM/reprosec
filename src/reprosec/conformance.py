from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .capsule import pack, verify_directory
from .models import CapsuleMetadata

REQUIRED_DIRS = {
    "actors",
    "environment",
    "workflow",
    "requests",
    "responses",
    "evidence",
    "assertions",
    "extractors",
    "timeline",
    "redactions",
    "provenance",
    "signatures",
    "reports",
}


@dataclass(frozen=True)
class ConformanceResult:
    conformant: bool
    schema_version: str | None
    checks: dict[str, bool]
    errors: list[str]


def check_conformance(root: Path) -> ConformanceResult:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    try:
        meta = CapsuleMetadata.model_validate_json((root / "capsule.json").read_text(encoding="utf-8"))
        schema = meta.schema_version
        checks["metadata_valid"] = True
    except Exception as exc:
        schema = None
        checks["metadata_valid"] = False
        errors.append(f"metadata invalid: {exc}")
    missing = sorted(name for name in REQUIRED_DIRS if not (root / name).is_dir())
    checks["required_layout"] = not missing
    if missing:
        errors.append(f"missing required directories: {', '.join(missing)}")
    integrity = verify_directory(root)
    checks["manifest_integrity"] = not integrity
    errors.extend(integrity)

    deterministic = False
    if checks["metadata_valid"] and checks["required_layout"]:
        try:
            with tempfile.TemporaryDirectory() as td:
                first = Path(td) / "a.rcap"
                second = Path(td) / "b.rcap"
                pack(root, first)
                pack(root, second)
                deterministic = hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
        except Exception as exc:
            errors.append(f"determinism check failed: {exc}")
    checks["deterministic_pack"] = deterministic
    if not deterministic:
        errors.append("binary deterministic pack check failed")
    return ConformanceResult(not errors, schema, checks, errors)
