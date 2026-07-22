from fastapi.testclient import TestClient
from reprosec.api import create_app


def test_web_ui_is_served() -> None:
    r = TestClient(create_app()).get("/")
    assert r.status_code == 200
    assert "ReproSec Capsule" in r.text
