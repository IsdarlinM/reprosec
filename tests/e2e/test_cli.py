from pathlib import Path
from typer.testing import CliRunner
from reprosec.cli import app

runner = CliRunner()


def test_help_variants() -> None:
    for args in (["--help"], ["-h"], ["help"]):
        r = runner.invoke(app, args)
        assert r.exit_code == 0, r.output
        assert "verify" in r.output and "replay" in r.output


def test_demo_offline(tmp_path: Path) -> None:
    r = runner.invoke(app, ["demo", "--output", str(tmp_path / "demo")])
    assert r.exit_code == 0, r.output
    assert '"network_requests_made": 0' in r.output


def test_sync_lineage_research_note_and_graph_query(tmp_path: Path) -> None:
    capsule = tmp_path / "demo"
    assert runner.invoke(app, ["demo", "--output", str(capsule)]).exit_code == 0
    synced = runner.invoke(app, ["sync-lineage", str(capsule)])
    assert synced.exit_code == 0, synced.output
    assert '"requests"' in synced.output
    note = runner.invoke(app, ["research-note", str(capsule), "--title", "Observation", "--body", "Synthetic evidence only"])
    assert note.exit_code == 0, note.output
    query = runner.invoke(app, ["query", str(capsule), "http_request"])
    assert query.exit_code == 0, query.output
    assert "http_request" in query.output
