from pathlib import Path

from fastapi.testclient import TestClient

from reprosec.api import create_app
from reprosec.capsule import add_request, initialize_directory
from reprosec.models import RequestRecord


def test_capabilities_and_workspace_readonly_views(tmp_path: Path) -> None:
    root = tmp_path / "capsule"
    initialize_directory(root, "API test")
    add_request(root, RequestRecord(method="GET", url="https://example.com/?access_token=secret"))
    client = TestClient(create_app())
    capabilities = client.get("/api/v1/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["ai_required"] is False
    inspect = client.get("/api/v1/workspace/inspect", params={"path": str(root)})
    assert inspect.status_code == 200
    assert inspect.json()["counts"]["requests"] == 1
    preview = client.get("/api/v1/workspace/redaction-preview", params={"path": str(root)})
    assert preview.status_code == 200
    assert preview.json()["applied"] is False
    timeline = client.get("/api/v1/workspace/timeline", params={"path": str(root)})
    assert timeline.status_code == 200
    assert timeline.json()[0]["type"] == "request"
