from fastapi.testclient import TestClient

from reprosec.api_all import create_app


def test_reprosec_mounts_shared_security_workspace_v3() -> None:
    client = TestClient(create_app())
    page = client.get("/workbench")
    assert page.status_code == 200
    assert "Security Workspace" in page.text
    assert 'class="global-rail"' in page.text
    assert 'class="panel jobs activity-panel"' in page.text

    catalog = client.get("/api/v1/workbench/catalog")
    assert catalog.status_code == 200
    payload = catalog.json()
    assert payload["ui_version"] == 3
    assert payload["product"] == "reprosec"
    assert payload["contract"]["complete"] is True
    assert payload["execution"]["shell"] is False
    assert payload["execution"]["user_supplied_argv"] is False
