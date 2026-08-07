from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator


DEFAULT_VOLATILE_HEADERS = {
    "date",
    "server-timing",
    "traceparent",
    "tracestate",
    "x-amzn-trace-id",
    "x-cloud-trace-context",
    "x-request-id",
    "x-runtime",
}


class ReplayObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str
    status_code: int = Field(ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = ""
    content_type: str | None = None


class StabilityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ignored_headers: set[str] = Field(default_factory=lambda: set(DEFAULT_VOLATILE_HEADERS))
    ignored_json_paths: set[str] = Field(default_factory=set)
    regex_substitutions: list[tuple[str, str]] = Field(default_factory=list)
    minimum_samples: int = Field(default=3, ge=2, le=100)
    maximum_flakiness: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("regex_substitutions")
    @classmethod
    def validate_regex_substitutions(
        cls, value: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        for pattern, _ in value:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"invalid regex substitution pattern: {pattern}") from exc
        return value


class StabilityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_count: int
    dominant_fingerprint_count: int
    flakiness_score: float = Field(ge=0.0, le=1.0)
    deterministic: bool
    stable_status: bool
    stable_headers: bool
    stable_body: bool
    volatile_headers: list[str] = Field(default_factory=list)
    volatile_json_paths: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


def _drop_json_path(value: Any, path: str) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return
    current = value
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return
        if current is None:
            return
    leaf = parts[-1]
    if isinstance(current, dict):
        current.pop(leaf, None)
    elif isinstance(current, list) and leaf.isdigit() and int(leaf) < len(current):
        current[int(leaf)] = None


def _flatten_json(value: Any, prefix: str = "") -> dict[str, str]:
    output: dict[str, str] = {}
    if isinstance(value, dict):
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            output.update(_flatten_json(value[key], path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}.{index}" if prefix else str(index)
            output.update(_flatten_json(item, path))
    else:
        output[prefix] = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return output


def _header_value(headers: dict[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def _canonical_body(
    observation: ReplayObservation, policy: StabilityPolicy
) -> tuple[str, dict[str, str]]:
    body = observation.body
    for pattern, replacement in policy.regex_substitutions:
        body = re.sub(pattern, replacement, body)
    content_type = (
        observation.content_type or _header_value(observation.headers, "content-type")
    ).lower()
    if "json" not in content_type:
        return body, {}
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return body, {}
    for path in policy.ignored_json_paths:
        _drop_json_path(parsed, path)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return canonical, _flatten_json(parsed)


def _canonical_headers(
    observation: ReplayObservation, policy: StabilityPolicy
) -> dict[str, str]:
    ignored = {name.lower() for name in policy.ignored_headers}
    return {
        name.lower(): value.strip()
        for name, value in observation.headers.items()
        if name.lower() not in ignored
    }


def _fingerprint(observation: ReplayObservation, policy: StabilityPolicy) -> str:
    body, _ = _canonical_body(observation, policy)
    payload = {
        "status": observation.status_code,
        "headers": _canonical_headers(observation, policy),
        "body": body,
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def analyze_stability(
    observations: Sequence[ReplayObservation], policy: StabilityPolicy | None = None
) -> StabilityReport:
    active_policy = policy or StabilityPolicy()
    if len(observations) < active_policy.minimum_samples:
        raise ValueError(
            f"at least {active_policy.minimum_samples} observations are required for stability analysis"
        )

    fingerprints = [_fingerprint(item, active_policy) for item in observations]
    dominant = Counter(fingerprints).most_common(1)[0][1]
    flakiness = 1.0 - dominant / len(observations)
    stable_status = len({item.status_code for item in observations}) == 1

    normalized_headers = [
        _canonical_headers(item, active_policy) for item in observations
    ]
    stable_headers = all(item == normalized_headers[0] for item in normalized_headers[1:])
    header_names = sorted({name for item in normalized_headers for name in item})
    volatile_headers = [
        name
        for name in header_names
        if len({item.get(name) for item in normalized_headers}) > 1
    ]

    bodies: list[str] = []
    flattened: list[dict[str, str]] = []
    for item in observations:
        body, values = _canonical_body(item, active_policy)
        bodies.append(body)
        flattened.append(values)
    stable_body = len(set(bodies)) == 1
    json_paths = sorted({path for item in flattened for path in item})
    volatile_paths = [
        path for path in json_paths if len({item.get(path) for item in flattened}) > 1
    ]

    deterministic = flakiness <= active_policy.maximum_flakiness
    reasons = [
        f"Dominant normalized response occurred {dominant}/{len(observations)} times.",
        f"Flakiness score: {flakiness:.4f}.",
    ]
    if volatile_headers:
        reasons.append("Volatile retained headers: " + ", ".join(volatile_headers) + ".")
    if volatile_paths:
        reasons.append("Volatile retained JSON paths: " + ", ".join(volatile_paths) + ".")
    if not deterministic:
        reasons.append("Assertions must not create VALIDATED findings from this sample set.")
    else:
        reasons.append("The normalized sample set is stable enough for deterministic assertions.")

    return StabilityReport(
        sample_count=len(observations),
        dominant_fingerprint_count=dominant,
        flakiness_score=round(flakiness, 6),
        deterministic=deterministic,
        stable_status=stable_status,
        stable_headers=stable_headers,
        stable_body=stable_body,
        volatile_headers=volatile_headers,
        volatile_json_paths=volatile_paths,
        reasons=reasons,
    )
