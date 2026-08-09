from typer.main import get_command

from reprosec.cli_all import BRAND, app
from sric.cli_style import build_banner


def test_reprosec_brand_identity() -> None:
    banner = build_banner(BRAND)
    product = banner.index("ReproSec Capsule :: v0.5.3")
    developer = banner.index("Developer: IsdarlinM")
    description = banner.index("Capture, sanitize, replay")
    assert product < developer < description
    assert "IsdarlinM ::" not in banner


def test_no_color_option_is_registered() -> None:
    command = get_command(app)
    assert any("--no-color" in getattr(param, "opts", ()) for param in command.params)
