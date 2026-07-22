import pytest

from reprosec.importers import import_curl


@pytest.mark.parametrize(
    "command",
    [
        "curl https://example.com/",
        "curl -L https://example.com/",
        "curl --location --compressed https://example.com/",
        "curl -I https://example.com/",
        "curl --head https://example.com/",
        "curl --http1.1 https://example.com/",
        "curl --http2 https://example.com/",
        "curl --max-time 10 https://example.com/",
        "curl --connect-timeout 3 https://example.com/",
        "curl --fail https://example.com/",
        "curl --fail-with-body https://example.com/",
        "curl -A 'Agent/1.0' https://example.com/",
        "curl -H 'Accept: application/json' https://example.com/",
        "curl -b 'session=secret' https://example.com/",
        "curl -X POST -d 'x=1' https://example.com/",
        "curl --request PUT --data-raw '{\"x\":1}' -H 'Content-Type: application/json' https://example.com/",
        "curl --data-binary 'hello' https://example.com/",
        "curl -G --data-urlencode 'q=a b' https://example.com/search",
        "curl -k https://example.com/",
        "curl --resolve example.com:443:203.0.113.1 https://example.com/",
    ],
)
def test_common_curl_commands_are_parseable_without_execution(command: str) -> None:
    request = import_curl(command)
    assert request.url.startswith("https://example.com")
    assert request.source == "imported"
