from __future__ import annotations

import sys

from . import cli_commands_runtime as _runtime
from . import cli_research_context as _research_context  # noqa: F401
from .api_vnext import create_app as create_vnext_app
from .cli import normalize_help_argv
from .cli_vnext import app

_runtime.create_app = create_vnext_app

__all__ = ["app", "run"]


def run() -> None:
    """Console entrypoint exposing the complete CLI and vNext local Web/API."""
    sys.argv[:] = normalize_help_argv(sys.argv)
    app()
