from typer.testing import CliRunner

from reprosec.cli_all import BRAND, app
from sric.cli_style import build_banner


def test_reprosec_brand_identity() -> None:
    banner = build_banner(BRAND)
    assert "ReproSec Capsule" in banner
    assert "Capture, sanitize, replay" in banner
    assert "IsdarlinM :: v0.5.2" in banner


def test_root_help_documents_no_color() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--no-color" in result.stdout
