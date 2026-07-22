from pathlib import Path

from reprosec.capsule import add_request, initialize_directory
from reprosec.diffing import diff_responses
from reprosec.models import Header, RequestRecord, ResponseRecord
from reprosec.redact import redact_capsule


def test_redact_preview_then_apply(tmp_path: Path) -> None:
    root = tmp_path / "c"
    initialize_directory(root, "redaction")
    req = RequestRecord(
        method="GET",
        url="https://example.com",
        headers=[Header(name="Authorization", value="Bearer top-secret")],
    )
    add_request(root, req)
    preview = redact_capsule(root, apply=False)
    assert preview.files_changed == 1
    assert "top-secret" in (root / "requests" / f"{req.request_id}.json").read_text()
    redact_capsule(root, apply=True)
    assert "top-secret" not in (root / "requests" / f"{req.request_id}.json").read_text()


def test_diff_uses_body_hashes_not_body_echo() -> None:
    a = ResponseRecord(request_id="R", status_code=200, body="secret-a")
    b = ResponseRecord(request_id="R", status_code=403, body="secret-b")
    diff = diff_responses(a, b)
    assert diff.status_changed and diff.body_changed
    assert "secret-a" not in diff.expected_body_sha256
