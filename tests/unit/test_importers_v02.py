from pathlib import Path

from reprosec.importers import import_curl, import_har


def test_common_curl_flags_are_imported_as_data() -> None:
    req = import_curl(
        "curl -L --max-time 5 --compressed --http2 --fail-with-body "
        "-A 'ResearchClient/1' -H 'Accept: application/json' https://example.com/api"
    )
    assert req.method == "GET"
    assert req.import_metadata["follow_redirects_requested"] is True
    assert req.import_metadata["max_time"] == 5.0
    assert any(h.name == "User-Agent" for h in req.headers)


def test_curl_network_overrides_are_never_silently_applied() -> None:
    req = import_curl("curl -k --resolve example.com:443:203.0.113.1 https://example.com/")
    overrides = req.import_metadata["network_overrides"]
    assert len(overrides) == 2
    assert {item["class"] for item in overrides} == {
        "TLS_VERIFICATION_OVERRIDE",
        "NETWORK_ROUTING_OVERRIDE",
    }


def test_curl_get_data_urlencode() -> None:
    req = import_curl("curl -G --data-urlencode 'q=a b' https://example.com/search")
    assert req.method == "GET"
    assert "q=a+b" in req.url


def test_import_redacts_url_and_json_body(tmp_path: Path) -> None:
    har = tmp_path / "secret.har"
    har.write_text(
        '{"log":{"entries":[{"request":{"method":"POST","url":"https://example.com/cb?access_token=TOPSECRET",'
        '"headers":[{"name":"Content-Type","value":"application/json"}],'
        '"postData":{"text":"{\\"password\\":\\"PASS123\\",\\"safe\\":\\"ok\\"}"}},'
        '"response":{"status":200,"headers":[],"content":{"text":"ok"}}}]}}'
    )
    reqs, _ = import_har(har)
    req = reqs[0]
    assert "TOPSECRET" not in req.url
    assert '"password":"PASS123"' not in (req.body or "")
    assert req.redacted is True
