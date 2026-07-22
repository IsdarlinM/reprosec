from reprosec.extractors import extract
from reprosec.models import ExtractorSpec, Header, ResponseRecord


def test_extractors_are_deterministic() -> None:
    response = ResponseRecord(
        response_id="RES-X",
        request_id="REQ-X",
        status_code=200,
        headers=[Header(name="X-Request-ID", value="abc"), Header(name="Set-Cookie", value="sid=xyz; HttpOnly")],
        body='{"document":{"id":123}}',
    )
    assert extract(ExtractorSpec(response_id="RES-X", name="RID", kind="header", selector="X-Request-ID"), response).value == "abc"
    assert extract(ExtractorSpec(response_id="RES-X", name="SID", kind="cookie", selector="sid", sensitive=True), response).value == "xyz"
    assert extract(ExtractorSpec(response_id="RES-X", name="DOC", kind="jsonpath", selector="$.document.id"), response).value == "123"
