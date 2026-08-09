from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from sric.updater import perform_product_update

from . import __version__
from .cli_vnext import app
from .sric_bootstrap import ensure_for_official_update


@app.command("update")
def update(
    check: bool = typer.Option(False, "--check", help="Check the official release channel only."),
    force: bool = typer.Option(
        False,
        "--force",
        help="Reinstall the official release even when that same version is already installed. Never downgrades.",
    ),
    manifest: Optional[str] = typer.Option(
        None, "--manifest", help="Advanced override: custom signed release manifest path or HTTPS URL."
    ),
    public_key: Optional[Path] = typer.Option(
        None, "--public-key", help="Advanced override: trusted Ed25519 key for a custom manifest."
    ),
) -> None:
    """Check/install ReproSec and keep its shared SRIC runtime compatible."""

    if check and force:
        typer.echo("--check and --force cannot be used together.", err=True)
        raise typer.Exit(2)
    custom_requested = bool(
        manifest
        or public_key
        or os.getenv("REPROSEC_RELEASE_MANIFEST_URL")
        or os.getenv("REPROSEC_RELEASE_PUBLIC_KEY")
    )
    try:
        if not check and not custom_requested:
            ensure_for_official_update()
        status = perform_product_update(
            expected_product="reprosec",
            current_version=__version__,
            check_only=check,
            force=force,
            manifest_source=manifest,
            public_key_path=public_key,
            manifest_env="REPROSEC_RELEASE_MANIFEST_URL",
            public_key_env="REPROSEC_RELEASE_PUBLIC_KEY",
        )
    except Exception as exc:
        typer.echo(f"Update verification failed; no product update was installed: {exc}", err=True)
        raise typer.Exit(6)
    typer.echo(json.dumps(status.__dict__, indent=2))
