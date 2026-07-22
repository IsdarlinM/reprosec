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

@app.command("timeline")
def timeline(capsule: Path) -> None:
    """Show a deterministic evidence timeline without inferring missing events."""
    events: list[dict[str, object]] = []
    for path in sorted((capsule / "requests").glob("*.json")):
        request_record = RequestRecord.model_validate_json(path.read_text(encoding="utf-8"))
        events.append({"observed_at": request_record.observed_at, "type": "request", "id": request_record.request_id, "method": request_record.method, "url": request_record.url})
    for path in sorted((capsule / "responses").glob("*.json")):
        response_record = ResponseRecord.model_validate_json(path.read_text(encoding="utf-8"))
        events.append({"observed_at": response_record.observed_at, "type": "response", "id": response_record.response_id, "request_id": response_record.request_id, "status": response_record.status_code})
    events.sort(key=lambda item: str(item["observed_at"]))
    typer.echo(json.dumps(events, indent=2))


@app.command("explain")
def explain(capsule: Path, request_id: str) -> None:
    """Show evidence lineage for a request without converting inference into a finding."""
    req = RequestRecord.model_validate_json((capsule / "requests" / f"{request_id}.json").read_text(encoding="utf-8"))
    steps = []
    for path in sorted((capsule / "workflow").glob("*.json")):
        step = WorkflowStep.model_validate_json(path.read_text(encoding="utf-8"))
        if step.request_id == request_id:
            steps.append(step.model_dump(mode="json"))
    responses = []
    for path in sorted((capsule / "responses").glob("*.json")):
        response = ResponseRecord.model_validate_json(path.read_text(encoding="utf-8"))
        if response.request_id == request_id:
            responses.append({"response_id": response.response_id, "status_code": response.status_code, "body_sha256": response.body_sha256})
    typer.echo(json.dumps({"request": req.model_dump(mode="json"), "workflow": steps, "responses": responses, "lineage": ["request", "workflow observation", "response evidence"]}, indent=2))


@app.command("matrix")
def matrix(capsule: Path) -> None:
    """Build an observed actor/operation matrix from stored evidence only."""
    typer.echo(json.dumps(observed_matrix(capsule), indent=2))




@app.command("sync-lineage")
def sync_lineage(capsule: Path) -> None:
    """Index RCAP requests/responses/workflow into SRIC lineage + temporal graph primitives."""
    if not capsule.is_dir():
        typer.echo("sync-lineage requires an unpacked capsule directory", err=True)
        raise typer.Exit(2)
    lineage = EvidenceLineage(capsule)
    graph = TemporalGraph(capsule)
    indexed = {"requests": 0, "responses": 0, "workflow": 0}

    def append_once(record: LineageRecord) -> None:
        try:
            lineage.explain(record.artifact_id)
        except KeyError:
            lineage.append(record)

    for path in sorted((capsule / "requests").glob("*.json")):
        req = RequestRecord.model_validate_json(path.read_text(encoding="utf-8"))
        artifact_id = f"request:{req.request_id}"
        append_once(LineageRecord(artifact_id=artifact_id, artifact_type="http_request", status="OBSERVED", source="reprosec", method="rcap_request", evidence_ids=[req.request_id]))
        graph.upsert_node(GraphNode(node_id=artifact_id, node_type="http_request", label=f"{req.method} {req.url}", source="reprosec", evidence_ids=[req.request_id], metadata={"method": req.method, "url": req.url}))
        indexed["requests"] += 1
    for path in sorted((capsule / "responses").glob("*.json")):
        res = ResponseRecord.model_validate_json(path.read_text(encoding="utf-8"))
        artifact_id = f"response:{res.response_id}"
        parent_id = f"request:{res.request_id}"
        append_once(LineageRecord(artifact_id=artifact_id, artifact_type="http_response", status="OBSERVED", source="reprosec", method="rcap_response", evidence_ids=[res.response_id], parent_ids=[parent_id]))
        graph.upsert_node(GraphNode(node_id=artifact_id, node_type="http_response", label=f"HTTP {res.status_code}", source="reprosec", evidence_ids=[res.response_id], metadata={"status_code": res.status_code, "request_id": res.request_id}))
        graph.upsert_edge(GraphEdge(source_node_id=artifact_id, target_node_id=parent_id, edge_type="response_to", discovery_method="rcap_link", evidence_ids=[res.response_id]))
        indexed["responses"] += 1
    for path in sorted((capsule / "workflow").glob("*.json")):
        step = WorkflowStep.model_validate_json(path.read_text(encoding="utf-8"))
        artifact_id = f"workflow:{step.step_id}"
        parent_id = f"request:{step.request_id}"
        append_once(LineageRecord(artifact_id=artifact_id, artifact_type="workflow_step", status=step.state, source="reprosec", method="workflow", parent_ids=[parent_id]))
        graph.upsert_node(GraphNode(node_id=artifact_id, node_type="workflow_step", label=step.step_id, source="reprosec", metadata={"actor": step.actor, "state": step.state}))
        graph.upsert_edge(GraphEdge(source_node_id=artifact_id, target_node_id=parent_id, edge_type="uses_request", discovery_method="workflow"))
        indexed["workflow"] += 1
    typer.echo(json.dumps(indexed, indent=2))


@app.command("research-note")
def research_note(
    capsule: Path,
    title: Optional[str] = typer.Option(None, "--title"),
    body: Optional[str] = typer.Option(None, "--body"),
    entry_type: str = typer.Option("observation", "--type"),
    status: str = typer.Option("OBSERVED", "--status"),
) -> None:
    """List or append a reproducible research-notebook entry inside an unpacked capsule."""
    notebook = ResearchNotebook(capsule)
    if title or body:
        if not (title and body):
            typer.echo("--title and --body are required together", err=True)
            raise typer.Exit(2)
        item = notebook.add(NotebookEntry(entry_type=entry_type, title=title, body=body, status=status))
        typer.echo(item.model_dump_json(indent=2))
        return
    typer.echo(json.dumps([x.model_dump(mode="json") for x in notebook.list()], indent=2, default=str))


@app.command("query")
def query_capsule(
    capsule: Path, query: str, limit: int = typer.Option(50, "--limit", min=1, max=500)
) -> None:
    """Search the SRIC graph previously produced by `reprosec sync-lineage`."""
    typer.echo(json.dumps(TemporalGraph(capsule).search(query, limit), indent=2, default=str))

@app.command("conformance")
def conformance(capsule: Path) -> None:
    """Run RCAP layout, integrity and deterministic-pack conformance checks."""
    result = check_conformance(capsule)
    typer.echo(json.dumps(asdict(result), indent=2))
    if not result.conformant:
        raise typer.Exit(5)


@app.command("report")
def report(
    capsule: Path,
    output: Path = typer.Option(..., "--output"),
    format: str = typer.Option("md", "--format"),
) -> None:
    """Export a report that separates evidence from interpretation."""
    write_report(capsule, output, format)
    typer.echo(str(output))


