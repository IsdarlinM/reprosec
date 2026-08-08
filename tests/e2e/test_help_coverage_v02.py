from typer.main import get_command
from typer.testing import CliRunner
from reprosec.cli_all import app


def test_registered_commands_support_short_and_long_help() -> None:
    runner = CliRunner()
    command = get_command(app)
    names = sorted(command.commands)  # type: ignore[attr-defined]
    assert names
    for name in names:
        assert runner.invoke(app, [name, "--help"]).exit_code == 0, name
        assert runner.invoke(app, [name, "-h"]).exit_code == 0, name
