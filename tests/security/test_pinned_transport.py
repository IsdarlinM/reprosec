from __future__ import annotations

from reprosec.transport import PinnedNetworkBackend


def test_pinned_backend_connects_to_validated_ip_not_hostname(monkeypatch) -> None:
    backend = PinnedNetworkBackend("example.com", ["93.184.216.34"])
    captured: list[tuple[str, int]] = []

    class FakeSocket:
        def setsockopt(self, *args):
            return None

    def fake_create_connection(address, timeout=None, source_address=None):
        captured.append(address)
        return FakeSocket()

    monkeypatch.setattr("reprosec.transport.socket.create_connection", fake_create_connection)
    backend.connect_tcp("example.com", 443)
    assert captured == [("93.184.216.34", 443)]
