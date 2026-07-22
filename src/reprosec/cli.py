from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import typer

from sric.policy import PolicyEngine
from sric.audit import AuditLogger
from sric.models import OperationMode
from sric.scope import ScopeEngine, ScopePolicy
from sric.updater import perform_update
from sric.graph import GraphEdge, GraphNode, TemporalGraph
from sric.lineage import EvidenceLineage, LineageRecord
from sric.notebook import NotebookEntry, ResearchNotebook

from . import __version__
from .api import create_app
from .assertions import evaluate
from .capsule import (
    add_assertion,
    add_extractor,
    add_request,
    add_response,
    add_workflow_step,
    build_manifest,
    initialize_directory,
    pack,
    safe_extract,
    verify_directory,
)
from .importers import import_curl, import_har, import_raw_http
from .models import AssertionSpec, ExtractorSpec, RequestRecord, ResponseRecord, WorkflowStep
from .replay import ReplayError, Replayer
from .report import write_report
from .redact import redact_capsule
from .diffing import as_safe_dict, diff_responses
from .extractors import extract as run_extractor
from .conformance import check_conformance
from .matrix import observed_matrix
from .signing import generate_keypair, sign_manifest, verify_signature

CTX = {"help_option_names": ["-h", "--help"]}
app = typer.Typer(
    name="reprosec",
    help="ReproSec Capsule — capture, sanitize, verify and replay evidence.",
    no_args_is_help=True,
    context_settings=CTX,
    rich_markup_mode=None,
)
import_app = typer.Typer(
    help="Import HAR, raw HTTP or curl into a capsule directory.", context_settings=CTX
)
workflow_app = typer.Typer(
    help="Build deterministic multi-actor workflow steps.", context_settings=CTX
)
key_app = typer.Typer(help="Generate and use local Ed25519 signing keys.", context_settings=CTX)
app.add_typer(import_app, name="import")
app.add_typer(workflow_app, name="workflow")
app.add_typer(key_app, name="key")



# Command modules register their Typer commands on the shared app.
from . import cli_commands_basic as _cli_commands_basic  # noqa: E402,F401
from . import cli_commands_replay as _cli_commands_replay  # noqa: E402,F401
from . import cli_commands_evidence as _cli_commands_evidence  # noqa: E402,F401
from . import cli_commands_runtime as _cli_commands_runtime  # noqa: E402,F401

@app.command("help", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def help_command(ctx: typer.Context, command: Optional[str] = typer.Argument(None)) -> None:
    """Show root or top-level command help."""
    if not command:
        typer.echo(ctx.parent.get_help() if ctx.parent else ctx.get_help())
        return
    root = ctx.parent.command if ctx.parent else app
    if hasattr(root, "commands") and command in root.commands:
        typer.echo(root.commands[command].get_help(ctx))
        return
    typer.echo(f"Unknown command: {command}", err=True)
    raise typer.Exit(2)


def normalize_help_argv(argv: list[str]) -> list[str]:
    """Normalize trailing `help` so root and nested commands share one help source."""
    normalized = list(argv)
    if len(normalized) >= 3 and normalized[-1] == "help" and normalized[1] != "help":
        normalized[-1] = "--help"
    return normalized


def run() -> None:
    """Console entrypoint supporting `reprosec COMMAND help`."""
    import sys

    sys.argv[:] = normalize_help_argv(sys.argv)
    app()
