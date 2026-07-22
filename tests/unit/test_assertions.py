from reprosec.assertions import evaluate
from reprosec.models import AssertionSpec, ResponseRecord


def test_status_assertion() -> None:
    r = ResponseRecord(request_id="REQ-1", status_code=200)
    a = AssertionSpec(request_id="REQ-1", kind="status_code", expected="200")
    assert evaluate(a, r).passed
