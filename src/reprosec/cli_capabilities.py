from __future__ import annotations

import json

import typer
from sric.capabilities import discover_capabilities

from .cli_vnext import app


@app.command("capabilities")
def capabilities_command() -> None:
    """Show standalone readiness and optional Sentinel Forge integrations."""

    report = discover_capabilities(current_product="reprosec")
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))
    if not report.standalone_ready:
        raise typer.Exit(2)
