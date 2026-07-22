from __future__ import annotations

import base64

import httpx
import pytest

from reprosec.models import RequestRecord
from reprosec.replay import ReplayError, Replayer
from sric.scope import ScopeEngine, ScopePolicy


class Stream:
    def get_extra_info(self, key: str):
        if key in {"server_addr", "peername"}:
            return ("93.184.216.34", 443)
        return None


class Response:
    def __init__(self, *, body: bytes, content_type: str, content_length: int | None = None) -> None:
        headers = [("content-type", content_type)]
        if content_length is not None:
            headers.append(("content-length", str(content_length)))
        self.headers = httpx.Headers(headers)
        self.body = body
        self.status_code = 200
        self.extensions = {"network_stream": Stream()}
        self.http_version = "HTTP/1.1"
        self.encoding = "utf-8"
        self.is_redirect = False
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def iter_bytes(self): yield self.body


class Client:
    response: Response
    def __init__(self, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def stream(self, *args, **kwargs): return self.response


def _replayer(monkeypatch: pytest.MonkeyPatch, response: Response, **kwargs) -> Replayer:
    Client.response = response
    monkeypatch.setattr("reprosec.replay.httpx.Client", Client)
    monkeypatch.setattr("reprosec.replay.resolve_ips", lambda _: ["93.184.216.34"])
    return Replayer(ScopeEngine(ScopePolicy(allow_targets=["example.com"])), **kwargs)


def test_declared_oversized_response_is_rejected_before_body_read(monkeypatch: pytest.MonkeyPatch) -> None:
    r = _replayer(monkeypatch, Response(body=b"x", content_type="text/plain", content_length=1000), max_download_bytes=10)
    with pytest.raises(ReplayError, match="Content-Length exceeds"):
        r.replay(RequestRecord(method="GET", url="https://example.com/"))


def test_binary_response_is_preserved_as_base64_with_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = b"\x00\x01\xffbinary"
    r = _replayer(monkeypatch, Response(body=raw, content_type="application/octet-stream", content_length=len(raw)))
    result = r.replay(RequestRecord(method="GET", url="https://example.com/"))
    assert result.response.body is None
    assert base64.b64decode(result.response.body_base64 or "") == raw
    assert result.response.body_sha256
    assert result.response.body_size_bytes == len(raw)


def test_retention_truncates_storage_but_hashes_full_observed_body(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = b"abcdefghij"
    r = _replayer(monkeypatch, Response(body=raw, content_type="text/plain", content_length=len(raw)), max_store_bytes=4, max_download_bytes=20)
    result = r.replay(RequestRecord(method="GET", url="https://example.com/"))
    assert result.response.body == "abcd"
    assert result.response.body_truncated is True
    assert result.response.body_size_bytes == 10
