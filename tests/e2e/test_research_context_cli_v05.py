import json
from pathlib import Path

from typer.testing import CliRunner

from reprosec.cli_all import app

runner = CliRunner()


def test_research_context_cli(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    path.write_text(
        json.dumps(
            {
                "sentinel_case_id": "case-1",
                "scope_snapshot": {
                    "snapshot_id": "scope-1",
                    "source": "test",
                    "allowed_hosts": ["example.test"],
                },
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["research-context", str(path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["scope_snapshot_id"] == "scope-1"
    assert len(payload["context_sha256"]) == 64
