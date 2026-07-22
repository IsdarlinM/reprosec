from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .models import ResponseRecord


@dataclass(frozen=True)
class ResponseDiff:
    status_changed: bool
    expected_status: int
    observed_status: int
    added_headers: list[str]
    removed_headers: list[str]
    changed_headers: list[str]
    body_changed: bool
    expected_body_sha256: str
    observed_body_sha256: str
    semantic_type: str | None = None
    semantic_changes: list[str] | None = None


def _hash_body(value: str | None) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def _walk_json(expected: Any, observed: Any, path: str = "$") -> list[str]:
    changes: list[str] = []
    if type(expected) is not type(observed):
        return [f"{path}: type changed {type(expected).__name__}->{type(observed).__name__}"]
    if isinstance(expected, dict):
        for key in sorted(expected.keys() - observed.keys()):
            changes.append(f"{path}.{key}: removed")
        for key in sorted(observed.keys() - expected.keys()):
            changes.append(f"{path}.{key}: added")
        for key in sorted(expected.keys() & observed.keys()):
            changes.extend(_walk_json(expected[key], observed[key], f"{path}.{key}"))
    elif isinstance(expected, list):
        if len(expected) != len(observed):
            changes.append(f"{path}: length {len(expected)}->{len(observed)}")
        for index, (left, right) in enumerate(zip(expected, observed)):
            changes.extend(_walk_json(left, right, f"{path}[{index}]"))
    elif expected != observed:
        changes.append(f"{path}: value changed")
    return changes


def diff_responses(expected: ResponseRecord, observed: ResponseRecord, *, semantic: bool = False) -> ResponseDiff:
    exp = {h.name.lower(): h.value for h in expected.headers}
    obs = {h.name.lower(): h.value for h in observed.headers}
    added = sorted(obs.keys() - exp.keys())
    removed = sorted(exp.keys() - obs.keys())
    changed = sorted(k for k in exp.keys() & obs.keys() if exp[k] != obs[k])
    exp_hash = expected.body_sha256 or _hash_body(expected.body)
    obs_hash = observed.body_sha256 or _hash_body(observed.body)
    semantic_type = None
    semantic_changes = None
    if semantic and expected.body is not None and observed.body is not None:
        try:
            semantic_changes = _walk_json(json.loads(expected.body), json.loads(observed.body))
            semantic_type = "json"
        except json.JSONDecodeError:
            semantic_type = "text"
            semantic_changes = [] if expected.body == observed.body else ["$: textual content changed"]
    return ResponseDiff(
        status_changed=expected.status_code != observed.status_code,
        expected_status=expected.status_code,
        observed_status=observed.status_code,
        added_headers=added,
        removed_headers=removed,
        changed_headers=changed,
        body_changed=exp_hash != obs_hash,
        expected_body_sha256=exp_hash,
        observed_body_sha256=obs_hash,
        semantic_type=semantic_type,
        semantic_changes=semantic_changes,
    )


def as_safe_dict(diff: ResponseDiff) -> dict[str, object]:
    return asdict(diff)
