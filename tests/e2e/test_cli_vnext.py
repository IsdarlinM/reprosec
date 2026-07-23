from typer.main import get_command
from typer.testing import CliRunner
from reprosec.cli_vnext import app


def test_vnext_cli_help_surface() -> None:
    runner=CliRunner(); root=get_command(app); commands=getattr(root,"commands",{}); assert commands
    for name in commands:
        assert runner.invoke(app,[name,"--help"]).exit_code==0,name
        assert runner.invoke(app,[name,"-h"]).exit_code==0,name
