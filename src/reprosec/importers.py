from __future__ import annotations

import base64
import hashlib
import json
import shlex
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

from sric.redaction import redact_body, redact_text, redact_url

from .models import Header, RequestRecord, ResponseRecord
from .security import MAX_IMPORT_BYTES, validate_external_url


def _read_limited(path: Path) -> bytes:
    if path.stat().st_size > MAX_IMPORT_BYTES:
        raise ValueError("import file exceeds size limit")
    return path.read_bytes()


def _content_type(headers: list[dict[str, str]] | list[Header]) -> str | None:
    for h in headers:
        name = h.name if isinstance(h, Header) else h.get("name", "")
        value = h.value if isinstance(h, Header) else h.get("value", "")
        if name.lower() == "content-type":
            return value
    return None


def _redact_headers(headers: list[dict[str, str]]) -> tuple[list[Header], bool]:
    result: list[Header] = []
    changed = False
    for h in headers:
        line = f"{h.get('name', '')}: {h.get('value', '')}"
        redacted = redact_text(line).text
        name, _, value = redacted.partition(":")
        changed = changed or redacted != line
        result.append(Header(name=name.strip(), value=value.strip()))
    return result, changed


def _redact_request_parts(
    url: str, headers: list[dict[str, str]], body: str | None
) -> tuple[str, list[Header], str | None, bool]:
    ur = redact_url(url)
    hs, changed = _redact_headers(headers)
    body_changed = False
    if body is not None:
        br = redact_body(body, _content_type(headers))
        body = br.text
        body_changed = bool(br.detected)
    return ur.text, hs, body, changed or body_changed or bool(ur.detected)


def import_har(path: Path) -> tuple[list[RequestRecord], list[ResponseRecord]]:
    raw = _read_limited(path)
    obj = json.loads(raw)
    entries = obj.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("invalid HAR: log.entries must be an array")
    requests: list[RequestRecord] = []
    responses: list[ResponseRecord] = []
    for entry in entries:
        req = entry.get("request", {})
        url = req.get("url", "")
        validate_external_url(url)
        post_data = req.get("postData", {})
        body = post_data.get("text") if isinstance(post_data, dict) else None
        url, headers, body, req_redacted = _redact_request_parts(url, req.get("headers", []), body)
        request = RequestRecord(
            method=req.get("method", "GET").upper(),
            url=url,
            headers=headers,
            body=body,
            media_type=_content_type(headers),
            source="imported",
            redacted=req_redacted,
            import_metadata={"format": "har"},
        )
        requests.append(request)
        res = entry.get("response", {})
        raw_res_headers = res.get("headers", [])
        res_headers, res_redacted = _redact_headers(raw_res_headers)
        content = res.get("content", {}) if isinstance(res.get("content", {}), dict) else {}
        res_body = content.get("text")
        body_base64 = None
        body_sha256 = None
        body_size = None
        media_type = content.get("mimeType") or _content_type(raw_res_headers)
        if res_body and content.get("encoding") == "base64":
            try:
                decoded = base64.b64decode(res_body, validate=True)
                body_sha256 = hashlib.sha256(decoded).hexdigest()
                body_size = len(decoded)
                if media_type and (media_type.startswith("text/") or "json" in media_type):
                    res_body = decoded.decode("utf-8", errors="replace")
                else:
                    body_base64 = base64.b64encode(decoded).decode("ascii")
                    res_body = None
            except Exception:
                res_body = "[invalid base64 content omitted]"
        if res_body:
            rr = redact_body(res_body, media_type)
            res_body = rr.text
            res_redacted |= bool(rr.detected)
            body_size = len(res_body.encode("utf-8"))
            body_sha256 = hashlib.sha256(res_body.encode("utf-8")).hexdigest()
        status = int(res.get("status", 0) or 0)
        if 100 <= status <= 599:
            responses.append(
                ResponseRecord(
                    request_id=request.request_id,
                    status_code=status,
                    headers=res_headers,
                    body=res_body,
                    body_base64=body_base64,
                    body_sha256=body_sha256,
                    body_size_bytes=body_size,
                    media_type=media_type,
                    redacted=res_redacted,
                )
            )
    return requests, responses


def import_raw_http(path: Path, *, scheme: str = "https", host: str | None = None) -> RequestRecord:
    text = _read_limited(path).decode("utf-8", errors="strict").replace("\r\n", "\n")
    head, _, body = text.partition("\n\n")
    lines = head.splitlines()
    if not lines:
        raise ValueError("empty HTTP request")
    parts = lines[0].split()
    if len(parts) < 2:
        raise ValueError("invalid HTTP request line")
    method, target = parts[0].upper(), parts[1]
    parsed_headers: list[dict[str, str]] = []
    host_header = host
    for line in lines[1:]:
        if ":" not in line:
            raise ValueError("invalid HTTP header line")
        name, value = line.split(":", 1)
        if name.lower() == "host":
            host_header = value.strip()
        parsed_headers.append({"name": name.strip(), "value": value.strip()})
    if target.startswith("http://") or target.startswith("https://"):
        url = target
    else:
        if not host_header:
            raise ValueError("raw request needs Host header or --host")
        url = f"{scheme}://{host_header}{target}"
    validate_external_url(url)
    url, headers, redacted_body, changed = _redact_request_parts(url, parsed_headers, body or None)
    return RequestRecord(
        method=method,
        url=url,
        headers=headers,
        body=redacted_body,
        media_type=_content_type(headers),
        source="imported",
        redacted=changed,
        import_metadata={"format": "raw-http"},
    )


def _require_value(tokens: list[str], index: int, option: str) -> tuple[str, int]:
    nxt = index + 1
    if nxt >= len(tokens):
        raise ValueError(f"curl option {option} requires a value")
    return tokens[nxt], nxt


def import_curl(command: str) -> RequestRecord:
    """Parse common curl syntax as untrusted data. No shell or subprocess is executed."""
    tokens = shlex.split(command)
    if not tokens or tokens[0] != "curl":
        raise ValueError("command must start with curl")
    method = "GET"
    headers: list[dict[str, str]] = []
    body: str | None = None
    url: str | None = None
    query_additions: list[tuple[str, str]] = []
    force_get = False
    metadata: dict[str, Any] = {"format": "curl", "options": [], "network_overrides": []}
    i = 1
    while i < len(tokens):
        t = tokens[i]
        if t in {"-X", "--request"}:
            method, i = _require_value(tokens, i, t)
            method = method.upper()
        elif t in {"-H", "--header"}:
            raw, i = _require_value(tokens, i, t)
            if ":" not in raw:
                raise ValueError("invalid curl header")
            n, v = raw.split(":", 1)
            headers.append({"name": n.strip(), "value": v.strip()})
        elif t in {"-d", "--data", "--data-raw", "--data-binary"}:
            raw, i = _require_value(tokens, i, t)
            body = raw
            metadata["options"].append(t)
            if method == "GET":
                method = "POST"
        elif t == "--data-urlencode":
            raw, i = _require_value(tokens, i, t)
            if "=" in raw:
                key, val = raw.split("=", 1)
                if force_get:
                    query_additions.append((key, val))
                else:
                    body = f"{body + '&' if body else ''}{urlencode([(key, val)])}"
            else:
                body = f"{body + '&' if body else ''}{raw}"
            metadata["options"].append(t)
            if not force_get:
                method = "POST"
        elif t in {"-A", "--user-agent"}:
            raw, i = _require_value(tokens, i, t)
            headers.append({"name": "User-Agent", "value": raw})
        elif t in {"-b", "--cookie"}:
            raw, i = _require_value(tokens, i, t)
            headers.append({"name": "Cookie", "value": raw})
        elif t in {"--url"}:
            raw, i = _require_value(tokens, i, t)
            if url is not None:
                raise ValueError("multiple URLs are not supported in one import")
            url = raw
        elif t in {"-L", "--location", "--compressed", "--http1.1", "--http2", "--fail", "--fail-with-body"}:
            metadata["options"].append(t)
            if t in {"-L", "--location"}:
                metadata["follow_redirects_requested"] = True
        elif t in {"-I", "--head"}:
            method = "HEAD"
            metadata["options"].append(t)
        elif t in {"-G", "--get"}:
            force_get = True
            method = "GET"
            metadata["options"].append(t)
        elif t in {"--max-time", "--connect-timeout"}:
            raw, i = _require_value(tokens, i, t)
            try:
                metadata[t.lstrip("-").replace("-", "_")] = float(raw)
            except ValueError as exc:
                raise ValueError(f"invalid numeric value for {t}") from exc
        elif t in {"-k", "--insecure"}:
            metadata["network_overrides"].append({"option": t, "class": "TLS_VERIFICATION_OVERRIDE"})
        elif t in {"--proxy", "-x", "--resolve", "--connect-to"}:
            raw, i = _require_value(tokens, i, t)
            metadata["network_overrides"].append(
                {"option": t, "value": raw, "class": "NETWORK_ROUTING_OVERRIDE"}
            )
        elif t in {"-F", "--form"}:
            raw, i = _require_value(tokens, i, t)
            metadata["form_fields"] = [*metadata.get("form_fields", []), raw]
            metadata["requires_manual_body_materialization"] = True
            if method == "GET":
                method = "POST"
        elif t.startswith("-"):
            raise ValueError(f"unsupported curl option: {t}")
        else:
            if url is not None:
                raise ValueError("multiple URLs are not supported in one import")
            url = t
        i += 1
    if not url:
        raise ValueError("curl command does not contain a URL")
    if query_additions:
        parsed = urlsplit(url)
        query = parsed.query
        extra = urlencode(query_additions)
        url = urlunsplit(parsed._replace(query=f"{query}&{extra}" if query else extra))
    validate_external_url(url)
    url, hs, body, changed = _redact_request_parts(url, headers, body)
    return RequestRecord(
        method=method,
        url=url,
        headers=hs,
        body=body,
        media_type=_content_type(hs),
        source="imported",
        redacted=changed,
        import_metadata=metadata,
    )
