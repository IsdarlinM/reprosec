from __future__ import annotations

import json
from pathlib import Path

import typer
from pydantic import ValidationError

from .cli_vnext import app
from .research_context import CapsuleResearchContext


@app.command("research-context")
def research_context(
    path: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    """Validate and inspect a Sentinel Forge RCAP research-context document."""

    try:
        context = CapsuleResearchContext.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        typer.echo(f"invalid research context: {exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(
        json.dumps(
            {
                "sentinel_case_id": context.sentinel_case_id,
                "scope_snapshot_id": (
                    context.scope_snapshot.snapshot_id
                    if context.scope_snapshot is not None
                    else None
                ),
                "policy_decision_count": len(context.policy_decisions),
                "validation_recipe_count": len(context.validation_recipes),
                "tool_provenance_count": len(context.tool_provenance),
                "counter_evidence_ids": context.counter_evidence_ids,
                "context_sha256": context.sha256(),
                "validated_finding_created": False,
            },
            indent=2,
        )
    )
