from __future__ import annotations

import typer
from sric.cli_style import CLIBrand, configure_cli_context, no_color_option, run_branded_cli

from . import __version__
from . import cli_commands_runtime as _runtime
from . import cli_research_context as _research_context  # noqa: F401
from .api_all import create_app as create_complete_app
from .cli import normalize_help_argv
from .cli_vnext import app
from . import cli_capabilities as _cli_capabilities  # noqa: F401
from . import cli_update as _cli_update  # noqa: F401,E402

_runtime.create_app = create_complete_app

__all__ = ["BRAND", "app", "run"]

BRAND = CLIBrand(
    product="ReproSec Capsule",
    description="Capture, sanitize, replay, and package reproducible security evidence.",
    version=__version__,
)
app.rich_markup_mode = "rich"


@app.callback()
def branded_main(
    ctx: typer.Context,
    no_color: bool = no_color_option(),
) -> None:
    """ReproSec CLI presentation controls."""

    configure_cli_context(ctx, no_color=no_color)


def run() -> None:
    """Console entrypoint exposing the complete branded CLI and local Web/API."""

    run_branded_cli(app, BRAND, argv_normalizer=normalize_help_argv)
