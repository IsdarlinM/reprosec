from __future__ import annotations

import json
from pathlib import Path

import typer
from pydantic import ValidationError

from .cli import CTX, app
from .controls import (
    ControlRole,
    DifferentialDesignPolicy,
    ExperimentSample,
    assess_differential_design,
)
from .protocols import (
    GraphQLOperationRecord,
    GrpcMessageRecord,
    ProtocolKind,
    WebSocketFrameRecord,
)
from .stability import ReplayObservation, StabilityPolicy, StabilityReport, analyze_stability

precision_app = typer.Typer(
    help="Evaluate replay determinism and differential-control completeness.",
    context_settings=CTX,
)
protocol_app = typer.Typer(
    help="Validate passive WebSocket, gRPC and GraphQL evidence records.",
    context_settings=CTX,
)
app.add_typer(precision_app, name="precision")
app.add_typer(protocol_app, name="protocol")


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"cannot read valid JSON from {path}: {exc}") from exc


def _validation_error(exc: Exception) -> typer.Exit:
    typer.echo(f"invalid analysis input: {exc}", err=True)
    return typer.Exit(2)


@precision_app.command("stability")
def stability_command(
    observations: Path,
    policy: Path | None = typer.Option(None, "--policy"),
) -> None:
    """Analyze repeated normalized responses and report flakiness."""
    raw = _read_json(observations)
    if not isinstance(raw, list):
        raise typer.BadParameter("observations JSON must be a list")
    try:
        values = [ReplayObservation.model_validate(item) for item in raw]
        active_policy = (
            StabilityPolicy.model_validate(_read_json(policy))
            if policy is not None
            else StabilityPolicy()
        )
        report = analyze_stability(values, active_policy)
    except (ValidationError, ValueError) as exc:
        raise _validation_error(exc) from exc
    typer.echo(report.model_dump_json(indent=2))
    if not report.deterministic:
        raise typer.Exit(2)


@precision_app.command("differential-check")
def differential_check_command(
    samples: Path,
    stability: Path,
    policy: Path | None = typer.Option(None, "--policy"),
) -> None:
    """Check baseline/control/repetition/reset prerequisites without validating."""
    raw_samples = _read_json(samples)
    raw_stability = _read_json(stability)
    if not isinstance(raw_samples, list):
        raise typer.BadParameter("samples JSON must be a list")
    if not isinstance(raw_stability, dict):
        raise typer.BadParameter("stability JSON must be an object keyed by role")
    try:
        values = [ExperimentSample.model_validate(item) for item in raw_samples]
        stability_values = {
            ControlRole(role): StabilityReport.model_validate(value)
            for role, value in raw_stability.items()
        }
        active_policy = (
            DifferentialDesignPolicy.model_validate(_read_json(policy))
            if policy is not None
            else DifferentialDesignPolicy()
        )
        report = assess_differential_design(
            values,
            policy=active_policy,
            stability_by_role=stability_values,
        )
    except (ValidationError, ValueError) as exc:
        raise _validation_error(exc) from exc
    typer.echo(report.model_dump_json(indent=2))
    if not report.ready_for_validation:
        raise typer.Exit(2)


@protocol_app.command("validate")
def protocol_validate_command(
    path: Path,
    kind: ProtocolKind = typer.Option(..., "--kind", case_sensitive=False),
) -> None:
    """Validate passive protocol records as untrusted data; never replay them."""
    raw = _read_json(path)
    records = raw if isinstance(raw, list) else [raw]
    model = {
        ProtocolKind.WEBSOCKET: WebSocketFrameRecord,
        ProtocolKind.GRPC: GrpcMessageRecord,
        ProtocolKind.GRAPHQL: GraphQLOperationRecord,
    }[kind]
    try:
        validated = [model.model_validate(item) for item in records]
    except ValidationError as exc:
        raise _validation_error(exc) from exc
    typer.echo(
        json.dumps(
            {
                "protocol": kind.value,
                "records": len(validated),
                "passive_only": True,
                "record_ids": [str(item.record_id) for item in validated],
            },
            indent=2,
        )
    )
