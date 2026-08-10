from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from sric.capabilities import discover_capabilities

from . import __version__
from .api_vnext import create_app as create_base_app
from .sric_bootstrap import status as sric_runtime_status


def _mount_degraded_workbench(app: FastAPI, reason: str) -> None:
    @app.get("/workbench", include_in_schema=False)
    async def workbench_unavailable() -> HTMLResponse:
        return HTMLResponse(
            "<h1>Sentinel Forge runtime repair required</h1>"
            "<p>The native ReproSec dashboard remains available, but the shared Web Feature "
            "Workbench cannot start because SRIC Core is incompatible.</p>"
            f"<pre>{reason}</pre><p>Run <code>reprosec doctor</code> and then "
            "<code>reprosec update</code>, or rerun the installer.</p>",
            status_code=503,
        )

    @app.get("/api/v1/workbench/coverage", include_in_schema=False)
    async def workbench_coverage_unavailable() -> JSONResponse:
        return JSONResponse(
            {
                "complete": False,
                "status": "RUNTIME_INCOMPATIBLE",
                "reason": reason,
                "repair": "reprosec update or rerun installer",
            },
            status_code=503,
        )


def create_app() -> FastAPI:
    app = create_base_app()

    @app.get("/api/v1/capabilities", tags=["standalone"])
    async def capabilities() -> dict[str, object]:
        return discover_capabilities(current_product="reprosec").model_dump(mode="json")

    @app.get("/api/v1/runtime-compatibility", tags=["standalone"])
    async def runtime_compatibility() -> dict[str, object]:
        runtime = sric_runtime_status()
        return {
            "compatible": runtime.compatible,
            "sric_version": runtime.version,
            "missing_modules": list(runtime.missing_modules),
            "reasons": list(runtime.reasons),
        }

    try:
        from sric.web_catalog import install_json_safe_catalog
        from sric.web_console import WebConsoleConfig, mount_web_console

        install_json_safe_catalog()
    except ModuleNotFoundError as exc:
        reason = f"missing shared Web console/catalog module: {exc.name or exc}"
        _mount_degraded_workbench(app, reason)
        return app

    config = WebConsoleConfig(
        product="reprosec",
        display_name="ReproSec Capsule",
        cli_module="reprosec.cli_all",
        version=__version__,
    )
    manager = mount_web_console(app, config)
    try:
        from sric.web_workbench import mount_feature_workbench
    except ModuleNotFoundError as exc:
        _mount_degraded_workbench(app, f"missing shared Workbench module: {exc.name or exc}")
    else:
        mount_feature_workbench(app, config, manager)
    return app
