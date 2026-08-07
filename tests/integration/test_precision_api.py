import hashlib

from fastapi.testclient import TestClient

from reprosec.api import create_app


def test_stability_api_reports_deterministic_repeated_responses() -> None:
    client = TestClient(create_app())
    body_hash = hashlib.sha256(b'{"ok":true}').hexdigest()
    observations = [
        {
            "observation_id": f"O-{index}",
            "status_code": 200,
            "headers": {"content-type": "application/json"},
            "body_sha256": body_hash,
            "body_text": '{"ok":true}',
            "evidence_ids": [f"E-{index}"],
        }
        for index in range(3)
    ]
    response = client.post(
        "/api/v1/precision/stability",
        json={"observations": observations},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deterministic"] is True
    assert payload["supports_validated_finding"] is True


def test_differential_api_missing_control_is_not_ready() -> None:
    client = TestClient(create_app())
    samples = []
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
