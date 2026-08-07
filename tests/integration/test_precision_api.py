from fastapi.testclient import TestClient

from reprosec.api import create_app


def _stable_observations(count: int = 3) -> list[dict[str, object]]:
    return [
        {
            "observation_id": f"O-{index}",
            "status_code": 200,
            "headers": {"Content-Type": "application/json", "X-Request-Id": str(index)},
            "body": '{"ok":true}',
        }
        for index in range(count)
    ]


def test_stability_api_reports_deterministic_repeated_responses() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/precision/stability",
        json={"observations": _stable_observations()},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["deterministic"] is True
    assert payload["sample_count"] == 3
    assert "VALIDATED findings" not in " ".join(payload["reasons"])


def test_stability_api_returns_422_for_insufficient_samples() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/precision/stability",
        json={"observations": _stable_observations(2)},
    )
    assert response.status_code == 422
    assert "at least 3 observations" in response.text


def test_differential_api_missing_control_is_not_ready() -> None:
    client = TestClient(create_app())
    samples: list[dict[str, object]] = []
    for role in ["BASELINE", "CANDIDATE"]:
        for index in range(3):
            samples.append(
                {
                    "sample_id": f"{role}-{index}",
                    "role": role,
                    "request_id": f"REQ-{role}-{index}",
                    "observation_id": f"OBS-{role}-{index}",
                    "actor_id": role.lower(),
                    "resource_id": "resource-1",
                    "resource_state": "active",
                    "session_age_bucket": "fresh",
                    "environment_id": "lab",
                    "sequence_index": len(samples),
                }
            )
    response = client.post(
        "/api/v1/precision/differential-check",
        json={"samples": samples, "stability_by_role": {}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ready_for_validation"] is False
    assert "NEGATIVE_CONTROL" in payload["missing_roles"]
    assert payload["status"] == "UNKNOWN"


def test_protocol_api_validates_records_without_execution() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/protocol/validate",
        json={
            "kind": "WEBSOCKET",
            "records": [
                {
                    "record_id": "WS-1",
                    "connection_id": "C-1",
                    "direction": "SERVER_TO_CLIENT",
                    "evidence_ids": ["E-1"],
                    "provenance_source": "capture",
                    "frame_index": 0,
                    "opcode": "TEXT",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["record_ids"] == ["WS-1"]
    assert payload["passive_only"] is True
    assert payload["executed"] is False


def test_protocol_api_returns_422_for_mismatched_record_type() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/protocol/validate",
        json={
            "kind": "WEBSOCKET",
            "records": [
                {
                    "record_id": "WS-X",
                    "protocol": "GRPC",
                    "connection_id": "C-1",
                    "direction": "SERVER_TO_CLIENT",
                    "evidence_ids": ["E-1"],
                    "provenance_source": "capture",
                    "frame_index": 0,
                    "opcode": "TEXT",
                }
            ],
        },
    )
    assert response.status_code == 422
