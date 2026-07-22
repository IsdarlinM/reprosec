from reprosec.assertions import evaluate
from reprosec.models import AssertionSpec, Header, ResponseRecord


def _response() -> ResponseRecord:
    return ResponseRecord(request_id="REQ-X", status_code=200, headers=[Header(name="X-Test", value="yes")], body='{"actor":{"id":"A"},"ok":true}')


def test_extended_assertions() -> None:
    response = _response()
    assert evaluate(AssertionSpec(request_id="REQ-X", kind="status_in", expected="200,201"), response).passed
    assert evaluate(AssertionSpec(request_id="REQ-X", kind="header_equals", selector="X-Test", expected="yes"), response).passed
    assert evaluate(AssertionSpec(request_id="REQ-X", kind="body_not_contains", expected="secret"), response).passed
    assert evaluate(AssertionSpec(request_id="REQ-X", kind="body_regex", expected='"ok":true'), response).passed
    assert evaluate(AssertionSpec(request_id="REQ-X", kind="jsonpath_equals", selector="$.actor.id", expected="A"), response).passed
