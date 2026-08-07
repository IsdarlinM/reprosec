from __future__ import annotations

import json
from pathlib import Path

import typer

from .capsule_analysis import CapsuleSnapshot, compare_capsules, plan_minimization
from .cli import CTX, app

capsule_analysis_app = typer.Typer(
    help="Compare capsule manifests and plan non-mutating minimization.",
    context_settings=CTX,
)
app.add_typer(capsule_analysis_app, name="capsule-analysis")


def _read_snapshot(path: Path) -> CapsuleSnapshot:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"cannot read valid JSON from {path}: {exc}") from exc
    return CapsuleSnapshot.model_validate(raw)


@capsule_analysis_app.command("compare")
def compare_command(
    before: Path,
    after: Path,
    include_unchanged: bool = typer.Option(False, "--include-unchanged"),
) -> None:
    """Compare deterministic artifact manifests without inferring impact."""

    report = compare_capsules(
        _read_snapshot(before),
        _read_snapshot(after),
        include_unchanged=include_unchanged,
    )
    typer.echo(report.model_dump_json(indent=2))


@capsule_analysis_app.command("minimize-plan")
def minimize_plan_command(
    snapshot: Path,
    root_artifact: list[str] = typer.Option(..., "--root-artifact"),
) -> None:
    """Plan dependency-safe retention; never mutate the capsule."""

    report = plan_minimization(
        _read_snapshot(snapshot),
        root_artifact_ids=root_artifact,
    )
    typer.echo(report.model_dump_json(indent=2))
    if report.missing_references:
        raise typer.Exit(2)
