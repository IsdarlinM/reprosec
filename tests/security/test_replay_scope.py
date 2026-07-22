import pytest

from reprosec.models import RequestRecord
from reprosec.replay import Replayer
from sric.scope import ScopeEngine, ScopePolicy


def test_out_of_scope_target_is_rejected_before_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_resolve(url: str) -> list[str]:
        nonlocal called
        called = True
        return ["93.184.216.34"]

    monkeypatch.setattr("reprosec.replay.resolve_ips", fake_resolve)
    req = RequestRecord(method="GET", url="https://outside.example.net/")
    replayer = Replayer(ScopeEngine(ScopePolicy(allow_targets=["*.example.com"])))

    with pytest.raises(PermissionError, match="scope denied replay"):
        replayer.replay(req)

    assert called is False, "out-of-scope targets must not trigger DNS resolution"
