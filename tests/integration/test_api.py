from fastapi.testclient import TestClient
from reprosec.api import create_app


def test_health_headers() -> None:
    r = TestClient(create_app()).get("/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
