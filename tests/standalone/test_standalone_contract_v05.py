from __future__ import annotations

import tomllib
from pathlib import Path

import click
from typer.main import get_command
from typer.testing import CliRunner

from reprosec.cli import normalize_help_argv
from reprosec.cli_all import app


ROOT = Path(__file__).resolve().parents[2]
OTHER_PRODUCTS = {"authtwin", "fossilscope", "trustboundary", "exposuredna"}
runner = CliRunner()


def _command_paths(command: click.Command, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    paths: list[tuple[str, ...]] = []
    if isinstance(command, click.Group):
        for name, child in command.commands.items():
            path = (*prefix, name)
            paths.append(path)
            paths.extend(_command_paths(child, path))
    return paths


def test_runtime_dependencies_do_not_require_sibling_products() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    runtime = [item.lower().replace(" ", "") for item in project["dependencies"]]
    assert any(item.startswith("sric-core") for item in runtime)
    for product in OTHER_PRODUCTS:
        assert not any(item.startswith(product) for item in runtime), product


def test_every_registered_command_path_supports_all_help_forms() -> None:
    command = get_command(app)
    for path in _command_paths(command):
        for flag in ("--help", "-h"):
            result = runner.invoke(app, [*path, flag])
            assert result.exit_code == 0, f"{' '.join(path)} {flag}: {result.output}"
        argv = normalize_help_argv(["reprosec", *path, "help"])
        result = runner.invoke(app, argv[1:])
        assert result.exit_code == 0, f"{' '.join(path)} help: {result.output}"


def test_safe_standalone_smokes() -> None:
    for args in (["version"], ["doctor"], ["capabilities"]):
        result = runner.invoke(app, list(args))
        assert result.exit_code == 0, f"{args}: {result.output}"
