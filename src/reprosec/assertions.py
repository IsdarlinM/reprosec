from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .models import AssertionSpec, ResponseRecord


@dataclass(frozen=True)
class AssertionResult:
    assertion_id: str
    passed: bool
    detail: str


def _jsonpath(obj: object, selector: str) -> object:
    path = selector.strip()
    if path.startswith("$."):
        path = path[2:]
    elif path == "$":
        return obj
    current = obj
    for part in path.split(".") if path else []:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(part)
    return current


def evaluate(spec: AssertionSpec, response: ResponseRecord) -> AssertionResult:
    if spec.request_id != response.request_id:
        return AssertionResult(spec.assertion_id, False, "assertion request_id does not match response")
    if spec.kind == "status_code":
        ok = str(response.status_code) == spec.expected
        return AssertionResult(spec.assertion_id, ok, f"observed status={response.status_code}")
    if spec.kind == "status_in":
        accepted = {int(x.strip()) for x in spec.expected.split(",") if x.strip()}
        ok = response.status_code in accepted
        return AssertionResult(spec.assertion_id, ok, f"observed status={response.status_code}")
    if spec.kind == "header_exists":
        ok = any(h.name.lower() == spec.expected.lower() for h in response.headers)
        return AssertionResult(spec.assertion_id, ok, f"header {spec.expected} {'present' if ok else 'absent'}")
    if spec.kind == "header_equals":
        if not spec.selector:
            raise ValueError("header_equals requires selector=header name")
        values = [h.value for h in response.headers if h.name.lower() == spec.selector.lower()]
        ok = spec.expected in values
        return AssertionResult(spec.assertion_id, ok, f"matched values={len(values)}")
    if spec.kind == "body_contains":
        ok = spec.expected in (response.body or "")
        return AssertionResult(spec.assertion_id, ok, "substring present" if ok else "substring absent")
    if spec.kind == "body_not_contains":
        ok = spec.expected not in (response.body or "")
        return AssertionResult(spec.assertion_id, ok, "substring absent" if ok else "substring present")
    if spec.kind == "body_regex":
        ok = re.search(spec.expected, response.body or "") is not None
        return AssertionResult(spec.assertion_id, ok, "regex matched" if ok else "regex did not match")
    if spec.kind in {"jsonpath_exists", "jsonpath_equals"}:
        if not spec.selector:
            raise ValueError(f"{spec.kind} requires selector")
        try:
            value = _jsonpath(json.loads(response.body or ""), spec.selector)
        except (json.JSONDecodeError, KeyError):
            return AssertionResult(spec.assertion_id, False, "JSONPath not found")
        if spec.kind == "jsonpath_exists":
            return AssertionResult(spec.assertion_id, True, "JSONPath exists")
        observed = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
        ok = observed == spec.expected
        return AssertionResult(spec.assertion_id, ok, "JSONPath equals expected" if ok else "JSONPath differs")
    raise ValueError(f"unsupported assertion kind: {spec.kind}")
