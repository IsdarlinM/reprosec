from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import typer

from sric.audit import AuditLogger
from sric.models import OperationMode
from sric.policy import PolicyEngine
from sric.scope import ScopeEngine, ScopePolicy

from . import __version__
from .assertions import evaluate
from .capsule import add_extractor, add_request, add_response, add_workflow_step
from .diffing import as_safe_dict, diff_responses
from .extractors import extract as run_extractor
from .models import AssertionSpec, ExtractorSpec, RequestRecord, ResponseRecord, WorkflowStep
from .redact import redact_capsule
from .replay import ReplayError, Replayer
from .cli import app

@app.command("replay")
def replay(
    capsule: Path,
    request_id: str,
    allow: list[str] = typer.Option(..., "--allow"),
    allow_network: list[str] = typer.Option([], "--allow-network"),
    allow_method: list[str] = typer.Option(["GET", "HEAD", "OPTIONS"], "--allow-method", help="Methods explicitly permitted by scope."),
    approve_action: bool = typer.Option(
        False, "--approve-action", "--approve-mutation",
        help="Explicitly approve an action that policy classifies as mutating/destructive.",
    ),
    bind: list[str] = typer.Option([], "--bind", help="Bind NAME=VALUE in memory; values are not stored."),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="Explicit proxy URL; environment proxies are ignored."),
    approve_proxy_routing: bool = typer.Option(False, "--approve-proxy-routing", help="Acknowledge that the proxy controls target resolution/routing."),
    follow_redirects: bool = typer.Option(False, "--follow-redirects", help="Follow redirects only after revalidating scope/DNS on every hop."),
    max_store_bytes: int = typer.Option(10 * 1024 * 1024, "--max-store-bytes", min=0),
    max_download_bytes: int = typer.Option(50 * 1024 * 1024, "--max-download-bytes", min=1),
    save_response: bool = typer.Option(False, "--save-response"),
) -> None:
    """Replay one request through Scope -> Policy -> Rate Limit -> Approval -> Executor."""
    bindings: dict[str, str] = {}
    for item in bind:
        if "=" not in item:
            raise typer.BadParameter("--bind values must use NAME=VALUE")
        name, value = item.split("=", 1)
        if not name:
            raise typer.BadParameter("--bind variable name cannot be empty")
        bindings[name] = value
    p = capsule / "requests" / f"{request_id}.json"
    req = RequestRecord.model_validate_json(p.read_text(encoding="utf-8"))
    engine = ScopeEngine(ScopePolicy(allow_targets=allow, allow_networks=allow_network, allowed_methods={m.upper() for m in allow_method}))
    audit = AuditLogger(capsule / "provenance" / "audit.jsonl")
    try:
        result = Replayer(
            engine,
            PolicyEngine(),
            proxy=proxy,
            allow_proxy_routing=approve_proxy_routing,
            follow_redirects=follow_redirects,
            audit_logger=audit,
            max_store_bytes=max_store_bytes,
            max_download_bytes=max_download_bytes,
        ).replay(req, human_approved=approve_action, bindings=bindings)
    except ReplayError as exc:
        audit.write(
            user="reprosec-user", action=f"{req.method.upper()} replay", target=req.url,
            policy_decision="error_or_denied", result=exc.code, tool_version=__version__,
        )
        typer.echo(
            json.dumps(
                {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "target": exc.target,
                    "hint": "Run `reprosec doctor --network`; use --debug only when diagnostics require a traceback.",
                },
                indent=2,
            ),
            err=True,
        )
        code = 3 if "SCOPE" in exc.code else 4 if any(x in exc.code for x in ("POLICY", "APPROVAL")) else 7
        raise typer.Exit(code)
    if save_response:
        add_response(capsule, result.response)
    typer.echo(result.response.model_dump_json(indent=2))


@app.command("check")
def check(capsule: Path, assertion_id: str, response_id: str) -> None:
    """Evaluate one deterministic assertion against one stored response."""
    spec = AssertionSpec.model_validate_json(
        (capsule / "assertions" / f"{assertion_id}.json").read_text(encoding="utf-8")
    )
    res = ResponseRecord.model_validate_json(
        (capsule / "responses" / f"{response_id}.json").read_text(encoding="utf-8")
    )
    typer.echo(json.dumps(asdict(evaluate(spec, res)), indent=2))


@app.command("redact")
def redact(
    capsule: Path,
    apply: bool = typer.Option(
        False, "--apply", help="Persist redactions after previewing detections."
    ),
) -> None:
    """Preview or apply secret redaction to stored request/response records."""
    preview = redact_capsule(capsule, apply=apply)
    typer.echo(json.dumps(asdict(preview), indent=2))


@app.command("diff")
def diff(
    capsule: Path,
    expected_response_id: str,
    observed_response_id: str,
    semantic: bool = typer.Option(False, "--semantic"),
) -> None:
    """Compare two responses without printing sensitive body content."""
    expected = ResponseRecord.model_validate_json(
        (capsule / "responses" / f"{expected_response_id}.json").read_text(encoding="utf-8")
    )
    observed = ResponseRecord.model_validate_json(
        (capsule / "responses" / f"{observed_response_id}.json").read_text(encoding="utf-8")
    )
    typer.echo(json.dumps(as_safe_dict(diff_responses(expected, observed, semantic=semantic)), indent=2))


@app.command("capture")
def capture(
    capsule: Path,
    url: str,
    allow: list[str] = typer.Option(..., "--allow"),
    method: str = typer.Option("GET", "--method"),
    allow_network: list[str] = typer.Option([], "--allow-network"),
    allow_method: list[str] = typer.Option(["GET", "HEAD", "OPTIONS"], "--allow-method"),
    approve_action: bool = typer.Option(False, "--approve-action"),
    follow_redirects: bool = typer.Option(False, "--follow-redirects"),
) -> None:
    """Capture one authorized HTTP interaction through the same safe replay gates."""
    req = RequestRecord(method=method.upper(), url=url, source="direct_capture")
    add_request(capsule, req)
    add_workflow_step(capsule, WorkflowStep(actor="Researcher", request_id=req.request_id, state="OBSERVED"))
    engine = ScopeEngine(ScopePolicy(allow_targets=allow, allow_networks=allow_network, allowed_methods={m.upper() for m in allow_method}))
    audit = AuditLogger(capsule / "provenance" / "audit.jsonl")
    try:
        result = Replayer(
            engine, PolicyEngine(), follow_redirects=follow_redirects, mode=OperationMode.OBSERVE,
            audit_logger=audit,
        ).replay(req, human_approved=approve_action)
    except ReplayError as exc:
        audit.write(user="reprosec-user", action=f"{method.upper()} capture", target=url, policy_decision="error_or_denied", result=exc.code, tool_version=__version__)
        typer.echo(json.dumps({"ok": False, "code": exc.code, "message": str(exc), "target": exc.target}, indent=2), err=True)
        raise typer.Exit(7)
    add_response(capsule, result.response)
    typer.echo(json.dumps({"request_id": req.request_id, "response_id": result.response.response_id, "status": result.response.status_code}, indent=2))


@app.command("extract")
def extract_value(
    capsule: Path,
    response_id: str,
    name: str,
    kind: str,
    selector: str,
    sensitive: bool = typer.Option(False, "--sensitive"),
    save_spec: bool = typer.Option(True, "--save-spec/--no-save-spec"),
    reveal: bool = typer.Option(False, "--reveal", help="Explicitly print a sensitive extracted value."),
) -> None:
    """Run a deterministic header/cookie/regex/JSONPath extractor."""
    response = ResponseRecord.model_validate_json((capsule / "responses" / f"{response_id}.json").read_text(encoding="utf-8"))
    spec = ExtractorSpec(response_id=response_id, name=name, kind=kind, selector=selector, sensitive=sensitive)  # type: ignore[arg-type]
    result = run_extractor(spec, response)
    if save_spec:
        add_extractor(capsule, spec)
    value = result.value if (not sensitive or reveal) else (f"${{{{{name}}}}}" if result.found else None)
    typer.echo(json.dumps({"extractor_id": spec.extractor_id, "name": name, "found": result.found, "value": value, "sensitive": sensitive}, indent=2))
