from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from .models import (
    CapsuleManifest,
    CapsuleMetadata,
    ManifestEntry,
    RequestRecord,
    ResponseRecord,
    WorkflowStep,
    AssertionSpec,
    ExtractorSpec,
)
from .security import MAX_ARCHIVE_ENTRIES, MAX_COMPRESSION_RATIO, MAX_TOTAL_UNCOMPRESSED

_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def initialize_directory(path: Path, title: str) -> CapsuleMetadata:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError("capsule directory is not empty")
    path.mkdir(parents=True, exist_ok=True)
    for sub in (
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
    ):
        (path / sub).mkdir()
    meta = CapsuleMetadata(title=title)
    _write_json(path / "capsule.json", meta.model_dump(mode="json"))
    (path / "capsule.yaml").write_text(
        f"format: RCAP\nschema_version: '0.2'\ncapsule_id: {meta.capsule_id}\ntitle: {json.dumps(title)}\n",
        encoding="utf-8",
    )
    return meta


def add_request(root: Path, req: RequestRecord) -> Path:
    p = root / "requests" / f"{req.request_id}.json"
    _write_json(p, req.model_dump(mode="json"))
    return p


def add_response(root: Path, res: ResponseRecord) -> Path:
    p = root / "responses" / f"{res.response_id}.json"
    _write_json(p, res.model_dump(mode="json"))
    return p


def add_workflow_step(root: Path, step: WorkflowStep) -> Path:
    p = root / "workflow" / f"{step.step_id}.json"
    _write_json(p, step.model_dump(mode="json"))
    return p


def add_assertion(root: Path, assertion: AssertionSpec) -> Path:
    p = root / "assertions" / f"{assertion.assertion_id}.json"
    _write_json(p, assertion.model_dump(mode="json"))
    return p



def add_extractor(root: Path, extractor: ExtractorSpec) -> Path:
    p = root / "extractors" / f"{extractor.extractor_id}.json"
    _write_json(p, extractor.model_dump(mode="json"))
    return p

def build_manifest(root: Path) -> CapsuleManifest:
    meta = CapsuleMetadata.model_validate_json((root / "capsule.json").read_text(encoding="utf-8"))
    entries = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel == "manifest.json" or rel.startswith("signatures/"):
            continue
        data = path.read_bytes()
        entries.append(ManifestEntry(path=rel, sha256=_sha(data), size_bytes=len(data)))
    manifest = CapsuleManifest(capsule_id=meta.capsule_id, entries=entries)
    _write_json(root / "manifest.json", manifest.model_dump(mode="json"))
    return manifest


def pack(root: Path, output: Path) -> Path:
    build_manifest(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=_FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())
    return output


def _safe_members(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    if len(infos) > MAX_ARCHIVE_ENTRIES:
        raise ValueError("archive has too many entries")
    total = 0
    for info in infos:
        p = PurePosixPath(info.filename)
        if p.is_absolute() or ".." in p.parts or "\\" in info.filename:
            raise ValueError("unsafe archive path")
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise ValueError("symlink entries are not allowed")
        total += info.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise ValueError("archive exceeds uncompressed size limit")
        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            raise ValueError("suspicious compression ratio")
    return infos


def safe_extract(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as zf:
        infos = _safe_members(zf)
        destination.mkdir(parents=True, exist_ok=True)
        base = destination.resolve()
        for info in infos:
            target = (destination / info.filename).resolve()
            if not str(target).startswith(str(base) + os.sep) and target != base:
                raise ValueError("archive path escapes destination")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
    return destination


def verify_directory(root: Path) -> list[str]:
    errors = []
    try:
        manifest = CapsuleManifest.model_validate_json(
            (root / "manifest.json").read_text(encoding="utf-8")
        )
    except Exception as exc:
        return [f"manifest invalid: {exc}"]
    for entry in manifest.entries:
        p = root / entry.path
        if not p.is_file():
            errors.append(f"missing: {entry.path}")
            continue
        data = p.read_bytes()
        if len(data) != entry.size_bytes:
            errors.append(f"size mismatch: {entry.path}")
        if _sha(data) != entry.sha256:
            errors.append(f"hash mismatch: {entry.path}")
    return errors


def verify_archive(archive: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        root = safe_extract(archive, Path(td))
        return verify_directory(root)
