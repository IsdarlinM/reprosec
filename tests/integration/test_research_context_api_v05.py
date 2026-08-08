from fastapi.testclient import TestClient

from reprosec.api_vnext import create_app


def test_research_context_api_returns_digest_without_validation() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/research-context/inspect",
        json={
            "sentinel_case_id": "case-1",
            "scope_snapshot": {
                "snapshot_id": "scope-1",
                "allowed_hosts": ["example.test"],
                "source": "program-policy",
            },
            "counter_evidence_ids": ["ev-counter"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["sentinel_case_id"] == "case-1"
    assert payload["scope_snapshot_id"] == "scope-1"
    assert len(payload["context_sha256"]) == 64
    assert payload["validated_finding_created"] is False
