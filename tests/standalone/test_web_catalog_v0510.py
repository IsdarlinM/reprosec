from fastapi.testclient import TestClient

from reprosec.api_all import create_app


def test_console_and_workbench_catalogs_are_http_json() -> None:
    client = TestClient(create_app())
    console = client.get("/console")
    assert console.status_code == 200
    styles = client.get("/console/styles.css")
    assert styles.status_code == 200
    catalog = client.get("/api/v1/console/catalog")
    assert catalog.status_code == 200
    assert catalog.json()["commands"]
    workbench = client.get("/workbench")
    assert workbench.status_code == 200
    feature_catalog = client.get("/api/v1/workbench/catalog")
    assert feature_catalog.status_code == 200
    assert feature_catalog.json()["features"]
    coverage = client.get("/api/v1/workbench/coverage")
    assert coverage.status_code == 200
    assert coverage.json()["complete"] is True
