from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import typer
from sric.scope import ScopeEngine, ScopePolicy
from sric.workspace import Workspace

from . import cli as base
from .browser import BrowserRecorder, BrowserRecordingSession
from .capture import CaptureRecorder, LocalCaptureProxy
from .capsule import add_actor, add_session, add_validation, add_request, add_response, add_workflow_step, initialize_directory
from .conformance import run_public_suite
from .diffing import diff_responses_v2
from .importers import import_burp_xml, import_zap_json
from .models import ActorRecord, SessionRecord, ValidationRecord, ResponseRecord, WorkflowStep
from .workflow_compiler import WorkflowCompiler

app=base.app
import_app=base.import_app
workflow_app=base.workflow_app
CTX={"help_option_names":["-h","--help"]}
capture_app=typer.Typer(help="Authorized/local evidence capture; capture never equals validation.",context_settings=CTX)
browser_app=typer.Typer(help="Import sanitized browser-recorder events.",context_settings=CTX)
actor_app=typer.Typer(help="Manage explicit RCAP actors and sessions.",context_settings=CTX)
app.add_typer(capture_app,name="capture")
app.add_typer(browser_app,name="browser")
app.add_typer(actor_app,name="actor")

@app.command("init")
def init_vnext(path:Path,title:str=typer.Option(...,"--title"),workspace:Optional[Path]=typer.Option(None,"--workspace"))->None:
    """Create RCAP 0.3 capsule, optionally linked to a shared SRIC workspace."""
    wid=str(Workspace.open(workspace).metadata.get("workspace_id")) if workspace else None
    typer.echo(initialize_directory(path,title,workspace_id=wid).model_dump_json(indent=2))

@import_app.command("burp")
def import_burp_cmd(path: Path, capsule: Path = typer.Option(..., "--capsule")) -> None:
    """Import a bounded Burp XML export as data; never execute requests."""
    reqs,resps=import_burp_xml(path)
    for r in reqs: add_request(capsule,r); add_workflow_step(capsule,WorkflowStep(actor="Actor A",request_id=r.request_id))
    for r in resps: add_response(capsule,r)
    typer.echo(json.dumps({"requests":len(reqs),"responses":len(resps)}))


@import_app.command("zap")
def import_zap_cmd(path: Path, capsule: Path = typer.Option(..., "--capsule")) -> None:
    """Import a bounded ZAP JSON/HAR export as data only."""
    reqs,resps=import_zap_json(path)
    for r in reqs: add_request(capsule,r); add_workflow_step(capsule,WorkflowStep(actor="Actor A",request_id=r.request_id))
    for r in resps: add_response(capsule,r)
    typer.echo(json.dumps({"requests":len(reqs),"responses":len(resps)}))


@actor_app.command("add")
def actor_add(capsule: Path, label: str, actor_type: str = typer.Option("user", "--type")) -> None:
    """Add an explicit actor without embedding credentials."""
    actor=ActorRecord(label=label,actor_type=actor_type);add_actor(capsule,actor);typer.echo(actor.model_dump_json(indent=2))


@actor_app.command("session")
def actor_session(capsule: Path, actor_id: str, label: str) -> None:
    """Create an actor-scoped session containing only opaque secret references."""
    session=SessionRecord(actor_id=actor_id,label=label);add_session(capsule,session);typer.echo(session.model_dump_json(indent=2))


@capture_app.command("request")
def capture_request(capsule: Path, method: str, url: str, allow: list[str] = typer.Option(...,"--allow"), actor_id: Optional[str]=typer.Option(None,"--actor"), session_id: Optional[str]=typer.Option(None,"--session"), approve_action: bool=typer.Option(False,"--approve-action")) -> None:
    """Capture one authorized HTTP exchange through Scope/Policy/RateLimit/Approval."""
    scope=ScopeEngine(ScopePolicy(allow_targets=allow,allowed_methods={method.upper()}))
    try:req,res=CaptureRecorder(capsule,scope).capture(method,url,actor_id=actor_id,session_id=session_id,approved=approve_action)
    except Exception as exc:typer.echo(f"capture denied/failed: {exc}",err=True);raise typer.Exit(3)
    typer.echo(json.dumps({"request_id":req.request_id,"response_id":res.response_id,"capture_is_validation":False},indent=2))


@capture_app.command("tls-tunnel")
def capture_tls_tunnel(capsule: Path, host: str, port: int = typer.Option(443,"--port"), actor_id: Optional[str]=typer.Option(None,"--actor"), session_id: Optional[str]=typer.Option(None,"--session")) -> None:
    """Record CONNECT/TLS tunnel metadata only; no silent MITM/decryption."""
    event=CaptureRecorder(capsule,ScopeEngine(ScopePolicy())).record_tls_tunnel(host,port,actor_id=actor_id,session_id=session_id);typer.echo(event.model_dump_json(indent=2))


@browser_app.command("import")
def browser_import(path: Path, capsule: Path=typer.Option(...,"--capsule"), actor_id: Optional[str]=typer.Option(None,"--actor"), session_id: Optional[str]=typer.Option(None,"--session")) -> None:
    """Import sanitized navigation/HTTP/WebSocket/storage/DOM events from JSONL."""
    events=BrowserRecorder(capsule).import_jsonl(path,actor_id=actor_id,session_id=session_id);typer.echo(json.dumps({"events":len(events)},indent=2))


@workflow_app.command("compile")
def workflow_compile(capsule: Path) -> None:
    """Compile candidate dependencies/extractors; deterministic replay is still required for proof."""
    typer.echo(json.dumps(WorkflowCompiler().compile(capsule),indent=2))


@app.command("diff-v2")
def diff_v2(capsule: Path, expected_response_id: str, observed_response_id: str) -> None:
    """Compare semantic/body/header/cookie/redirect/timing/network differences."""
    expected=ResponseRecord.model_validate_json((capsule/"responses"/f"{expected_response_id}.json").read_text())
    observed=ResponseRecord.model_validate_json((capsule/"responses"/f"{observed_response_id}.json").read_text())
    from dataclasses import asdict
    typer.echo(json.dumps(asdict(diff_responses_v2(expected,observed)),indent=2,default=str))


@app.command("validation-record")
def validation_record(capsule: Path, result: str, evidence: list[str]=typer.Option([],"--evidence"), request_id: Optional[str]=typer.Option(None,"--request-id"), deterministic: bool=typer.Option(True,"--deterministic/--non-deterministic")) -> None:
    """Record deterministic validation evidence separately from capture/AI hypotheses."""
    if result not in {"VALIDATED","REJECTED","UNKNOWN"}:raise typer.BadParameter("result must be VALIDATED, REJECTED or UNKNOWN")
    if result=="VALIDATED" and (not deterministic or not evidence):raise typer.BadParameter("VALIDATED requires deterministic evidence")
    rec=ValidationRecord(result=result,evidence_ids=evidence,request_id=request_id,deterministic=deterministic);add_validation(capsule,rec);typer.echo(rec.model_dump_json(indent=2))


@app.command("conformance-suite")
def conformance_suite() -> None:
    """Run the public self-contained RCAP 0.3 conformance matrix."""
    payload=run_public_suite();typer.echo(json.dumps(payload,indent=2));
    if payload["passed"]!=payload["total"]:raise typer.Exit(1)


@capture_app.command("proxy")
def capture_proxy(capsule: Path, allow: list[str] = typer.Option(...,"--allow"), host: str=typer.Option("127.0.0.1","--host"), port: int=typer.Option(8787,"--port"), approve_mutating: bool=typer.Option(False,"--approve-mutating")) -> None:
    """Run loopback HTTP capture proxy. CONNECT records metadata only; no silent TLS MITM."""
    scope=ScopeEngine(ScopePolicy(allow_targets=allow,allowed_methods={"GET","HEAD","OPTIONS","POST","PUT","PATCH","DELETE"}))
    try:LocalCaptureProxy(capsule,scope,host=host,port=port,approve_mutating=approve_mutating).serve()
    except ValueError as exc:typer.echo(str(exc),err=True);raise typer.Exit(2)


@browser_app.command("start")
def browser_start(capsule: Path, actor_id: Optional[str]=typer.Option(None,"--actor"), session_id: Optional[str]=typer.Option(None,"--session")) -> None:
    """Start a controlled browser-recorder lifecycle marker."""
    typer.echo(json.dumps(BrowserRecordingSession(capsule).start(actor_id=actor_id,session_id=session_id),indent=2))


@browser_app.command("stop")
def browser_stop(capsule: Path) -> None:
    """Stop the controlled browser-recorder lifecycle marker."""
    typer.echo(json.dumps(BrowserRecordingSession(capsule).stop(),indent=2))


@browser_app.command("status")
def browser_status(capsule: Path) -> None:
    """Show recorder lifecycle state without exposing secrets."""
    typer.echo(json.dumps(BrowserRecordingSession(capsule).status(),indent=2))

def run()->None:
    base.run()
