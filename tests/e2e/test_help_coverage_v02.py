from typer.main import get_command
from typer.testing import CliRunner

from reprosec.cli_vnext import app
from reprosec.cli import normalize_help_argv

runner = CliRunner()


def test_every_registered_root_command_has_dash_help_variants() -> None:
    root = get_command(app)
    commands = getattr(root, "commands", {})
    assert commands
    for name in sorted(commands):
        if name == "help":
            continue
        for flag in ("--help", "-h"):
            result = runner.invoke(app, [name, flag])
            assert result.exit_code == 0, f"{name} {flag}: {result.output}"


def test_trailing_help_normalization_supports_root_and_nested_commands() -> None:
    assert normalize_help_argv(["reprosec", "replay", "help"])[-1] == "--help"
    assert normalize_help_argv(["reprosec", "import", "har", "help"])[-1] == "--help"
    assert normalize_help_argv(["reprosec", "help"]) == ["reprosec", "help"]
