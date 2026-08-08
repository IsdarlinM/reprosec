from __future__ import annotations

from fastapi import FastAPI
from sric.capabilities import discover_capabilities

from .api_vnext import create_app as create_base_app


def create_app() -> FastAPI:
    app = create_base_app()

    @app.get("/api/v1/capabilities", tags=["standalone"])
    async def capabilities() -> dict[str, object]:
        return discover_capabilities(current_product="reprosec").model_dump(mode="json")

    return app
