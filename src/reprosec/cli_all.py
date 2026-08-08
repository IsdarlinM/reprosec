from __future__ import annotations

import sys

from . import cli_commands_runtime as _runtime
from . import cli_research_context as _research_context  # noqa: F401
from .api_all import create_app as create_complete_app
from .cli import normalize_help_argv
from .cli_vnext import app
from . import cli_capabilities as _cli_capabilities  # noqa: F401

_runtime.create_app = create_complete_app

__all__ = ["app", "run"]


def run() -> None:
    """Console entrypoint exposing the complete CLI and local Web/API."""
    sys.argv[:] = normalize_help_argv(sys.argv)
    app()
