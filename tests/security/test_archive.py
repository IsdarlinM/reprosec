from reprosec.importers import import_curl
import pytest


def test_rejects_curl_shell_features() -> None:
    with pytest.raises(ValueError):
        import_curl("curl --config /tmp/evil https://example.com")
