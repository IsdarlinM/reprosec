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
from .capsule import add_assertion, add_extractor, add_request, add_response, add_workflow_step, build_manifest, initialize_directory, pack, safe_extract, verify_directory
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
from .cli import app, import_app, workflow_app, key_app

@app.command("version")
def version() -> None:
    typer.echo(__version__)


@app.command("init")
def init(path: Path, title: str = typer.Option(..., "--title")) -> None:
    """Create a new unpacked RCAP workspace."""
    meta = initialize_directory(path, title)
    typer.echo(meta.model_dump_json(indent=2))


@import_app.command("har")
def import_har_cmd(path: Path, capsule: Path = typer.Option(..., "--capsule")) -> None:
    """Import requests/responses from a HAR. Sensitive headers are redacted."""
    reqs, resps = import_har(path)
    for imported_request in reqs:
        add_request(capsule, imported_request)
        add_workflow_step(capsule, WorkflowStep(actor="Actor A", request_id=imported_request.request_id))
    for imported_response in resps:
        add_response(capsule, imported_response)
    typer.echo(json.dumps({"requests": len(reqs), "responses": len(resps)}))


@import_app.command("raw")
def import_raw_cmd(
    path: Path,
    capsule: Path = typer.Option(..., "--capsule"),
    scheme: str = typer.Option("https", "--scheme"),
    host: Optional[str] = typer.Option(None, "--host"),
) -> None:
    """Import a raw HTTP request without executing it."""
    r = import_raw_http(path, scheme=scheme, host=host)
    add_request(capsule, r)
    add_workflow_step(capsule, WorkflowStep(actor="Actor A", request_id=r.request_id))
    typer.echo(r.request_id)


@import_app.command("curl")
def import_curl_cmd(command: str, capsule: Path = typer.Option(..., "--capsule")) -> None:
    """Parse a constrained curl command as data; the command is never executed."""
    r = import_curl(command)
    add_request(capsule, r)
    add_workflow_step(capsule, WorkflowStep(actor="Actor A", request_id=r.request_id))
    typer.echo(r.request_id)


@app.command("inspect")
def inspect(capsule: Path) -> None:
    """Inspect capsule metadata and file counts without replaying traffic."""
    root = capsule
    tmp = None
    if capsule.suffix == ".rcap":
        tmp = tempfile.TemporaryDirectory()
        root = safe_extract(capsule, Path(tmp.name))
    meta = json.loads((root / "capsule.json").read_text(encoding="utf-8"))
    meta["counts"] = {
        d: len(list((root / d).glob("*.json")))
        for d in ("requests", "responses", "workflow", "assertions", "extractors")
    }
    typer.echo(json.dumps(meta, indent=2))
    if tmp:
        tmp.cleanup()


@app.command("assertion")
def assertion(
    capsule: Path,
    request_id: str,
    kind: str,
    expected: str,
    selector: Optional[str] = typer.Option(None, "--selector"),
) -> None:
    """Add a deterministic assertion. Use --selector for header/JSONPath assertions."""
    spec = AssertionSpec(
        request_id=request_id, kind=kind, expected=expected, selector=selector  # type: ignore[arg-type]
    )
    add_assertion(capsule, spec)
    typer.echo(spec.assertion_id)


@workflow_app.command("add")
def workflow_add(
    capsule: Path,
    actor: str,
    request_id: str,
    depends_on: list[str] = typer.Option([], "--depends-on"),
    state: str = typer.Option("OBSERVED", "--state"),
) -> None:
    """Add a workflow step with explicit actor, dependencies and truth state."""
    step = WorkflowStep(actor=actor, request_id=request_id, depends_on=depends_on, state=state)  # type: ignore[arg-type]
    add_workflow_step(capsule, step)
    typer.echo(step.step_id)


@app.command("pack")
def pack_cmd(capsule: Path, output: Path = typer.Option(..., "--output")) -> None:
    """Create a deterministic .rcap ZIP container and manifest."""
    if output.suffix != ".rcap":
        raise typer.BadParameter("output must end with .rcap")
    pack(capsule, output)
    typer.echo(str(output))


@app.command("verify")
def verify(capsule: Path, public_key: Optional[Path] = typer.Option(None, "--public-key")) -> None:
    """Verify schema-facing manifest hashes and optional Ed25519 signature."""
    tmp = None
    root = capsule
    errors = []
    try:
        if capsule.suffix == ".rcap":
            tmp = tempfile.TemporaryDirectory()
            root = safe_extract(capsule, Path(tmp.name))
        errors = verify_directory(root)
        sig = None
        if public_key:
            try:
                sig = verify_signature(root, public_key)
            except Exception as exc:
                errors.append(f"signature invalid: {exc}")
                sig = False
        typer.echo(
            json.dumps({"valid": not errors, "signature_valid": sig, "errors": errors}, indent=2)
        )
    except Exception as exc:
        typer.echo(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        raise typer.Exit(5)
    finally:
        if tmp:
            tmp.cleanup()
    if errors:
        raise typer.Exit(5)


@key_app.command("generate")
def key_generate(
    private_key: Path = typer.Option(..., "--private"),
    public_key: Path = typer.Option(..., "--public"),
) -> None:
    """Generate a local Ed25519 keypair. Private keys are never uploaded."""
    if private_key.exists() or public_key.exists():
        raise typer.BadParameter("refusing to overwrite existing key file")
    generate_keypair(private_key, public_key)
    typer.echo("keypair generated")


@app.command("sign")
def sign(capsule: Path, private_key: Path = typer.Option(..., "--private-key")) -> None:
    """Build the manifest and sign it with a local Ed25519 private key."""
    build_manifest(capsule)
    out = sign_manifest(capsule, private_key)
    typer.echo(str(out))


