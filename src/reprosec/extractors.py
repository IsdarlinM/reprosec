from __future__ import annotations

import json
import re
from dataclasses import dataclass
from http.cookies import SimpleCookie

from .models import ExtractorSpec, ResponseRecord


@dataclass(frozen=True)
class ExtractionResult:
    extractor_id: str
    name: str
    found: bool
    value: str | None
    sensitive: bool


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


def extract(spec: ExtractorSpec, response: ResponseRecord) -> ExtractionResult:
    if spec.response_id != response.response_id:
        return ExtractionResult(spec.extractor_id, spec.name, False, None, spec.sensitive)
    value: str | None = None
    if spec.kind == "header":
        for header in response.headers:
            if header.name.lower() == spec.selector.lower():
                value = header.value
                break
    elif spec.kind == "cookie":
        for header in response.headers:
            if header.name.lower() != "set-cookie":
                continue
            cookie = SimpleCookie()
            cookie.load(header.value)
            if spec.selector in cookie:
                value = cookie[spec.selector].value
                break
    elif spec.kind == "regex":
        match = re.search(spec.selector, response.body or "")
        if match:
            value = match.group(1) if match.lastindex else match.group(0)
    elif spec.kind == "jsonpath":
        try:
            obj = json.loads(response.body or "")
            extracted = _jsonpath(obj, spec.selector)
            value = extracted if isinstance(extracted, str) else json.dumps(extracted, separators=(",", ":"))
        except (json.JSONDecodeError, KeyError):
            value = None
    else:
        raise ValueError(f"unsupported extractor kind: {spec.kind}")
    return ExtractionResult(spec.extractor_id, spec.name, value is not None, value, spec.sensitive)
