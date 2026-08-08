from typer.main import get_command

from reprosec.cli_all import BRAND, app
from sric.cli_style import build_banner


def test_reprosec_brand_identity() -> None:
    banner = build_banner(BRAND)
    assert "ReproSec Capsule" in banner
    assert "Capture, sanitize, replay" in banner
    assert "IsdarlinM :: v0.5.2" in banner


def test_no_color_option_is_registered() -> None:
    command = get_command(app)
    assert any("--no-color" in getattr(param, "opts", ()) for param in command.params)
