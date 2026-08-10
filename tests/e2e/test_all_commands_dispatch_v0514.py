from __future__ import annotations

from types import SimpleNamespace

import click
from typer.main import get_command
from typer.testing import CliRunner

import reprosec.cli_update as cli_update
from reprosec.cli_all import app


runner = CliRunner()


def _leaf_paths(command: click.Command, prefix: tuple[str, ...] = ()) -> list[str]:
    if not isinstance(command, click.Group):
        return [" ".join(prefix)]
    leaves: list[str] = []
    for name, child in command.commands.items():
        leaves.extend(_leaf_paths(child, (*prefix, name)))
    return sorted(leaves)


def test_every_public_command_dispatches_without_traceback(monkeypatch) -> None:
    """Run every public command entrypoint through real parsing/validation.

    Commands needing domain fixtures may stop at Typer's controlled usage boundary (exit 2).
    No network/server operation is allowed in this exhaustive dispatch gate; deeper E2E tests
    exercise successful domain paths separately.
    """

    monkeypatch.setattr(
        cli_update,
        "perform_product_update",
        lambda **_kwargs: SimpleNamespace(
            current_version="0.5.14",
            available_version="0.5.14",
            update_available=False,
            same_version=True,
            forced=False,
            installed=False,
            product="reprosec",
            artifact="fixture",
            channel="test",
        ),
    )
    monkeypatch.setattr("uvicorn.run", lambda *_args, **_kwargs: None)

    paths = _leaf_paths(get_command(app))
    assert paths
    for path in paths:
        args = path.split()
        if path == "update":
            args.append("--check")
        result = runner.invoke(app, args)
        assert result.exit_code in {0, 2, 3, 4, 6}, (
            f"{path} returned unexpected exit {result.exit_code}\n{result.output}\n{result.exception}"
        )
        assert "Traceback" not in result.output, path
