import hashlib

from fastapi.testclient import TestClient

from reprosec.api_vnext import create_app


def artifact(
    artifact_id: str,
    content: bytes,
    references: list[str] | None = None,
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "path": f"records/{artifact_id}.json",
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "record_type": "record",
        "references": references or [],
        "evidence_ids": [f"E-{artifact_id}"],
    }


def snapshot(
    capsule_id: str,
    artifacts: list[dict[str, object]],
) -> dict[str, object]:
    return {"capsule_id": capsule_id, "schema_version": "0.3", "artifacts": artifacts}


def test_capsule_compare_api_creates_no_findings() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/capsule-analysis/compare",
        json={
            "before": snapshot("before", [artifact("A", b"one")]),
            "after": snapshot("after", [artifact("A", b"two")]),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["MODIFIED"] == 1
    assert payload["findings_created"] == 0


def test_minimization_api_returns_non_mutating_plan() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/capsule-analysis/minimize-plan",
        json={
            "snapshot": snapshot(
                "capsule",
                [
                    artifact("request", b"request", ["response"]),
                    artifact("response", b"response"),
                    artifact("unused", b"unused"),
                ],
            ),
            "root_artifact_ids": ["request"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["retained_artifact_ids"] == ["request", "response"]
    assert payload["removable_artifact_ids"] == ["unused"]
    assert payload["applied"] is False


def test_minimization_api_rejects_empty_or_unknown_roots_without_500() -> None:
    client = TestClient(create_app())
    value = snapshot("capsule", [artifact("request", b"request")])

    empty = client.post(
        "/api/v1/capsule-analysis/minimize-plan",
        json={"snapshot": value, "root_artifact_ids": []},
    )
    assert empty.status_code == 422

    unknown = client.post(
        "/api/v1/capsule-analysis/minimize-plan",
        json={"snapshot": value, "root_artifact_ids": ["missing"]},
    )
    assert unknown.status_code == 422
    assert "unknown root artifact IDs" in unknown.text
