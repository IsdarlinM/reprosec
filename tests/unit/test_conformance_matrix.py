from pathlib import Path

from reprosec.capsule import add_request, add_response, add_workflow_step, build_manifest, initialize_directory
from reprosec.conformance import check_conformance
from reprosec.matrix import observed_matrix
from reprosec.models import RequestRecord, ResponseRecord, WorkflowStep


def test_conformance_and_observed_matrix(tmp_path: Path) -> None:
    root = tmp_path / "c"
    initialize_directory(root, "Conformance")
    request = RequestRecord(method="GET", url="https://example.com/doc/1")
    add_request(root, request)
    add_response(root, ResponseRecord(request_id=request.request_id, status_code=200))
    add_workflow_step(root, WorkflowStep(actor="Actor A", request_id=request.request_id))
    build_manifest(root)
    conformance = check_conformance(root)
    assert conformance.conformant
    assert conformance.checks["deterministic_pack"]
    matrix = observed_matrix(root)
    assert matrix["actors"]["Actor A"]["GET /doc/1"] == 200
