from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from sric.updater import perform_update

from . import __version__
from .api import create_app
from .capsule import (
    add_assertion,
    add_request,
    add_response,
    add_workflow_step,
    build_manifest,
    initialize_directory,
)
from .models import AssertionSpec, RequestRecord, ResponseRecord, WorkflowStep
from .cli import app

@app.command("doctor")
def doctor(
    network: bool = typer.Option(False, "--network", help="Diagnose DNS/proxy/network prerequisites without replaying a target request."),
    dns_name: str = typer.Option("example.com", "--dns-name"),
) -> None:
    """Check runtime, dependencies, safe defaults and optional network prerequisites."""
    import os
    import socket
    import sys
    import sric
    import cryptography

    payload: dict[str, object] = {
        "ok": sys.version_info >= (3, 11),
        "python": sys.version.split()[0],
        "sric": getattr(sric, "__version__", "unknown"),
        "cryptography": cryptography.__version__,
        "cloud_ai": "off",
        "telemetry": "off",
        "http_env_proxies_ignored_by_default": True,
    }
    if network:
        proxy_vars = {
            key: bool(os.getenv(key))
            for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")
        }
        try:
            addresses = sorted({row[4][0] for row in socket.getaddrinfo(dns_name, None, type=socket.SOCK_STREAM)})
            dns = {"ok": True, "name": dns_name, "addresses": addresses}
        except socket.gaierror as exc:
            dns = {"ok": False, "name": dns_name, "error": str(exc)}
            payload["ok"] = False
        payload["network"] = {"dns": dns, "proxy_environment_present": proxy_vars, "target_http_requests_sent": 0}
    typer.echo(json.dumps(payload, indent=2))
    raise typer.Exit(0 if payload["ok"] else 1)


@app.command("update")
def update(
    check: bool = typer.Option(
        False, "--check", help="Verify release metadata and only report availability."
    ),
    manifest: Optional[str] = typer.Option(
        None, "--manifest", help="Signed release manifest path or HTTPS URL."
    ),
    public_key: Optional[Path] = typer.Option(
        None, "--public-key", help="Trusted Ed25519 release public key."
    ),
) -> None:
    """Check or install a signed wheel release; never performs a blind git pull."""
    import os

    source = manifest or os.getenv("REPROSEC_RELEASE_MANIFEST_URL")
    key = public_key or (
        Path(os.environ["REPROSEC_RELEASE_PUBLIC_KEY"])
        if os.getenv("REPROSEC_RELEASE_PUBLIC_KEY")
        else None
    )
    if not source or key is None:
        typer.echo(
            "No trusted release channel configured. Provide --manifest and --public-key, "
            "or REPROSEC_RELEASE_MANIFEST_URL/REPROSEC_RELEASE_PUBLIC_KEY.",
            err=True,
        )
        raise typer.Exit(2)
    try:
        status = perform_update(
            manifest_source=source,
            public_key_path=key,
            expected_product="reprosec",
            current_version=__version__,
            check_only=check,
        )
    except Exception as exc:
        typer.echo(f"Update verification failed; no update was installed: {exc}", err=True)
        raise typer.Exit(6)
    typer.echo(json.dumps(status.__dict__, indent=2))


@app.command("web")
def web(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8770, "--port", min=1, max=65535),
) -> None:
    """Run the local API. Non-loopback binding remains disabled until authenticated TLS mode is implemented."""
    if host not in {"127.0.0.1", "localhost", "::1"}:
        typer.echo(
            "Non-loopback binding denied: authenticated TLS mode is not configured.",
            err=True,
        )
        raise typer.Exit(4)
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)


@app.command("demo")
def demo(output: Path = typer.Option(Path("reprosec-demo"), "--output")) -> None:
    """Create an offline synthetic two-actor capsule that demonstrates evidence lineage."""
    meta = initialize_directory(output, "Synthetic authorization evidence demo")
    a = RequestRecord(
        method="GET", url="https://lab.invalid/doc/123", headers=[], source="user_input"
    )
    add_request(output, a)
    add_workflow_step(
        output, WorkflowStep(actor="Owner", request_id=a.request_id, state="OBSERVED")
    )
    b = RequestRecord(
        method="GET", url="https://lab.invalid/doc/123", headers=[], source="user_input"
    )
    add_request(output, b)
    add_workflow_step(
        output,
        WorkflowStep(
            actor="OtherUser",
            request_id=b.request_id,
            depends_on=[a.request_id],
            state="HYPOTHESIS",
        ),
    )
    add_response(
        output,
        ResponseRecord(request_id=a.request_id, status_code=200, body='{"id":123,"owner":"A"}'),
    )
    add_assertion(
        output, AssertionSpec(request_id=a.request_id, kind="status_code", expected="200")
    )
    build_manifest(output)
    typer.echo(
        json.dumps(
            {"demo": str(output), "capsule_id": meta.capsule_id, "network_requests_made": 0},
            indent=2,
        )
    )
