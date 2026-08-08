from fastapi.testclient import TestClient

from reprosec.api_all import create_app


def test_standalone_web_and_capability_api() -> None:
    client = TestClient(create_app())
    root = client.get("/")
    assert root.status_code == 200
    report = client.get("/api/v1/capabilities")
    assert report.status_code == 200
    assert report.json()["current_product"] == "reprosec"
    assert report.json()["standalone_ready"] is True
