from typer.main import get_command
from typer.testing import CliRunner

from reprosec.cli_all import app


runner = CliRunner()


def test_update_exposes_force_option() -> None:
    update = get_command(app).commands["update"]
    assert any("--force" in getattr(param, "opts", ()) for param in update.params)


def test_update_rejects_check_plus_force_before_channel_resolution() -> None:
    result = runner.invoke(app, ["update", "--check", "--force"])
    assert result.exit_code == 2
    assert "--check and --force cannot be used together" in result.output
    assert "Traceback" not in result.output
