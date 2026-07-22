from __future__ import annotations

import httpx
import pytest

from reprosec.models import RequestRecord
from reprosec.replay import ReplayDeniedError, ReplayError, Replayer
from sric.scope import ScopeEngine, ScopePolicy


class FakeStream:
    def __init__(self, peer: str) -> None:
        self.peer = peer

    def get_extra_info(self, key: str):
        if key in {"server_addr", "peername"}:
            return (self.peer, 443)
        return None


class FakeResponse:
    def __init__(self, peer: str = "93.184.216.34") -> None:
        self.status_code = 200
        self.headers = httpx.Headers({"content-type": "application/json", "content-length": "11"})
        self.extensions = {"network_stream": FakeStream(peer)}
        self.http_version = "HTTP/2"
        self.encoding = "utf-8"
        self.is_redirect = False
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def iter_bytes(self): yield b'{"ok":true}'


class FakeClient:
    kwargs: dict[str, object] = {}
    peer = "93.184.216.34"
    def __init__(self, **kwargs) -> None: FakeClient.kwargs = kwargs
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def stream(self, *args, **kwargs): return FakeResponse(self.peer)


def test_replay_ignores_environment_proxies_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reprosec.replay.httpx.Client", FakeClient)
    monkeypatch.setattr("reprosec.replay.resolve_ips", lambda _: ["93.184.216.34"])
    result = Replayer(ScopeEngine(ScopePolicy(allow_targets=["example.com"]))).replay(RequestRecord(method="GET", url="https://example.com/"))
    assert FakeClient.kwargs["trust_env"] is False
    assert result.response.network and result.response.network.peer_ip == "93.184.216.34"


def test_peer_change_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reprosec.replay.httpx.Client", FakeClient)
    monkeypatch.setattr("reprosec.replay.resolve_ips", lambda _: ["93.184.216.34"])
    FakeClient.peer = "93.184.216.35"
    with pytest.raises(ReplayDeniedError, match="prevalidated/pinned DNS set"):
        Replayer(ScopeEngine(ScopePolicy(allow_targets=["example.com"]))).replay(RequestRecord(method="GET", url="https://example.com/"))
    FakeClient.peer = "93.184.216.34"


def test_unresolved_variable_fails_before_network(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False
    def resolve(_: str):
        nonlocal called; called = True; return ["93.184.216.34"]
    monkeypatch.setattr("reprosec.replay.resolve_ips", resolve)
    with pytest.raises(ReplayError, match="unresolved"):
        Replayer(ScopeEngine(ScopePolicy(allow_targets=["example.com"]))).replay(RequestRecord(method="GET", url="https://example.com/${{ID}}"))
    assert called is False


def test_delete_requires_destructive_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reprosec.replay.httpx.Client", FakeClient)
    monkeypatch.setattr("reprosec.replay.resolve_ips", lambda _: ["93.184.216.34"])
    scope = ScopeEngine(ScopePolicy(allow_targets=["example.com"], allowed_methods={"DELETE"}))
    with pytest.raises(ReplayDeniedError, match="approval"):
        Replayer(scope).replay(RequestRecord(method="DELETE", url="https://example.com/resource/1"))


def test_proxy_routing_requires_separate_explicit_approval() -> None:
    with pytest.raises(ReplayDeniedError, match="proxy routing requires explicit approval"):
        Replayer(ScopeEngine(ScopePolicy(allow_targets=["example.com"])), proxy="http://127.0.0.1:8080")
