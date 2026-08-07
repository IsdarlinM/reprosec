from collections.abc import Iterator
from pathlib import Path

import click
from typer.main import get_command
from typer.testing import CliRunner

from reprosec.cli import normalize_help_argv
from reprosec.cli_all import app

runner = CliRunner()


def command_paths() -> Iterator[list[str]]:
    root = get_command(app)

    def walk(group: click.Group, prefix: list[str]) -> Iterator[list[str]]:
        for name, command in sorted(group.commands.items()):
            path = [*prefix, name]
            yield path
            if isinstance(command, click.Group):
                yield from walk(command, path)

    if isinstance(root, click.Group):
        yield from walk(root, [])


def test_help_variants_use_real_entrypoint() -> None:
    for args in (["--help"], ["-h"], ["help"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert "verify" in result.output
        assert "replay" in result.output
        assert "precision" in result.output
        assert "protocol" in result.output
        assert "capsule-analysis" in result.output


def test_every_registered_command_supports_short_and_long_help() -> None:
    paths = list(command_paths())
    assert paths
    for path in paths:
        for flag in ("--help", "-h"):
            result = runner.invoke(app, [*path, flag])
            assert result.exit_code == 0, f"{path} {flag}: {result.output}"
            assert "Traceback" not in result.output


def test_trailing_help_normalization_works_at_every_depth() -> None:
    for path in command_paths():
        argv = ["reprosec", *path, "help"]
        normalized = normalize_help_argv(argv)
        assert normalized[-1] == "--help"
        assert normalized[:-1] == argv[:-1]


def test_demo_offline(tmp_path: Path) -> None:
    result = runner.invoke(app, ["demo", "--output", str(tmp_path / "demo")])
    assert result.exit_code == 0, result.output
    assert '"network_requests_made": 0' in result.output


def test_sync_lineage_research_note_and_graph_query(tmp_path: Path) -> None:
    capsule = tmp_path / "demo"
    assert runner.invoke(app, ["demo", "--output", str(capsule)]).exit_code == 0
    synced = runner.invoke(app, ["sync-lineage", str(capsule)])
    assert synced.exit_code == 0, synced.output
    assert '"requests"' in synced.output
    note = runner.invoke(
        app,
        [
            "research-note",
            str(capsule),
            "--title",
            "Observation",
            "--body",
            "Synthetic evidence only",
        ],
    )
    assert note.exit_code == 0, note.output
    query = runner.invoke(app, ["query", str(capsule), "http_request"])
    assert query.exit_code == 0, query.output
    assert "http_request" in query.output
