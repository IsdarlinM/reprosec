from __future__ import annotations

from fastapi import FastAPI
from sric.capabilities import discover_capabilities
from sric.web_console import WebConsoleConfig, mount_web_console
from sric.web_workbench import mount_feature_workbench

from . import __version__
from .api_vnext import create_app as create_base_app


def create_app() -> FastAPI:
    app = create_base_app()

    @app.get("/api/v1/capabilities", tags=["standalone"])
    async def capabilities() -> dict[str, object]:
        return discover_capabilities(current_product="reprosec").model_dump(mode="json")

    config = WebConsoleConfig(
        product="reprosec",
        display_name="ReproSec Capsule",
        cli_module="reprosec.cli_all",
        version=__version__,
    )
    manager = mount_web_console(app, config)
    mount_feature_workbench(app, config, manager)
    return app
