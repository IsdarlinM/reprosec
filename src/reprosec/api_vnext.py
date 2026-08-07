from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .api import create_app as create_base_app
from .capsule_analysis import CapsuleSnapshot, compare_capsules, plan_minimization


class CapsuleComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    before: CapsuleSnapshot
    after: CapsuleSnapshot
    include_unchanged: bool = False


class CapsuleMinimizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot: CapsuleSnapshot
    root_artifact_ids: list[str] = Field(min_length=1)


router = APIRouter(prefix="/api/v1/capsule-analysis", tags=["capsule-analysis"])


@router.post("/compare")
async def compare(request: CapsuleComparisonRequest) -> dict[str, object]:
    return compare_capsules(
        request.before,
        request.after,
        include_unchanged=request.include_unchanged,
    ).model_dump(mode="json")


@router.post("/minimize-plan")
async def minimize(request: CapsuleMinimizationRequest) -> dict[str, object]:
    try:
        report = plan_minimization(
            request.snapshot,
            root_artifact_ids=request.root_artifact_ids,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return report.model_dump(mode="json")


def create_app() -> FastAPI:
    app = create_base_app()
    app.include_router(router)
    return app
