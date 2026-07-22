from reprosec.diffing import diff_responses
from reprosec.models import ResponseRecord


def test_semantic_json_diff_reports_paths_without_values() -> None:
    expected = ResponseRecord(request_id="REQ", status_code=200, body='{"role":"user","id":1}')
    observed = ResponseRecord(request_id="REQ", status_code=200, body='{"role":"admin","id":1,"new":true}')
    diff = diff_responses(expected, observed, semantic=True)
    assert diff.semantic_type == "json"
    assert "$.role: value changed" in (diff.semantic_changes or [])
    assert "$.new: added" in (diff.semantic_changes or [])
    assert "admin" not in " ".join(diff.semantic_changes or [])
