from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sric.redaction import redact_body, redact_text, redact_url

from .models import RequestRecord, ResponseRecord


@dataclass(frozen=True)
class RedactionPreview:
    files_scanned: int
    files_changed: int
    detections: dict[str, int]


def _merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def _content_type(record: RequestRecord | ResponseRecord) -> str | None:
    if record.media_type:
        return record.media_type
    for header in record.headers:
        if header.name.lower() == "content-type":
            return header.value
    return None


def _redact_record(
    record: RequestRecord | ResponseRecord,
) -> tuple[RequestRecord | ResponseRecord, dict[str, int]]:
    counts: dict[str, int] = {}
    changed = False
    if isinstance(record, RequestRecord):
        result = redact_url(record.url)
        _merge_counts(counts, result.detected)
        if result.detected:
            record.url = result.text
            changed = True
    for header in record.headers:
        if header.value.startswith("${{REDACTED_"):
            continue
        result = redact_text(f"{header.name}: {header.value}")
        _merge_counts(counts, result.detected)
        if result.detected:
            _, _, value = result.text.partition(":")
            header.value = value.strip()
            changed = True
    if record.body:
        result = redact_body(record.body, _content_type(record))
        _merge_counts(counts, result.detected)
        if result.detected:
            record.body = result.text
            changed = True
    if changed:
        record.redacted = True
    return record, counts


def redact_capsule(root: Path, *, apply: bool = False) -> RedactionPreview:
    detections: dict[str, int] = {}
    files_scanned = 0
    files_changed = 0
    for directory, model in (("requests", RequestRecord), ("responses", ResponseRecord)):
        for path in sorted((root / directory).glob("*.json")):
            files_scanned += 1
            record = model.model_validate_json(path.read_text(encoding="utf-8"))
            updated, counts = _redact_record(record)
            if counts:
                files_changed += 1
                _merge_counts(detections, counts)
                if apply:
                    path.write_text(
                        json.dumps(updated.model_dump(mode="json"), indent=2, sort_keys=True)
                        + "\n",
                        encoding="utf-8",
                    )
    return RedactionPreview(files_scanned, files_changed, detections)
