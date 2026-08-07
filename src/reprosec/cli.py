from __future__ import annotations

from typing import Optional

import typer

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

from . import cli_commands_basic as _cli_commands_basic  # noqa: E402,F401
from . import cli_commands_capsule_analysis as _cli_commands_capsule_analysis  # noqa: E402,F401
from . import cli_commands_evidence as _cli_commands_evidence  # noqa: E402,F401
from . import cli_commands_precision as _cli_commands_precision  # noqa: E402,F401
from . import cli_commands_replay as _cli_commands_replay  # noqa: E402,F401
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
