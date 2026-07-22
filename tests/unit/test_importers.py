from pathlib import Path
from reprosec.importers import import_curl, import_har, import_raw_http


def test_curl_is_parsed_not_executed() -> None:
    r = import_curl("curl -H 'Authorization: Bearer secret' https://example.com/a")
    assert r.method == "GET" and r.redacted and "secret" not in r.headers[0].value


def test_raw_http(tmp_path: Path) -> None:
    p = tmp_path / "r.txt"
    p.write_text("GET /x HTTP/1.1\r\nHost: example.com\r\nCookie: a=b\r\n\r\n")
    r = import_raw_http(p)
    assert r.url == "https://example.com/x" and r.redacted


def test_har(tmp_path: Path) -> None:
    p = tmp_path / "x.har"
    p.write_text('{"log":{"entries":[{"request":{"method":"GET","url":"https://example.com","headers":[]},"response":{"status":200,"headers":[],"content":{"text":"ok"}}}]}}')
    req, res = import_har(p)
    assert len(req) == 1 and res[0].request_id == req[0].request_id
