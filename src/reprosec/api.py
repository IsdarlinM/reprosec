from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .capsule import safe_extract, verify_archive
from .controls import (
    ControlRole,
    DifferentialDesignPolicy,
    ExperimentSample,
    assess_differential_design,
)
from .models import CapsuleMetadata, RequestRecord, ResponseRecord
from .protocols import (
    GraphQLOperationRecord,
    GrpcMessageRecord,
    ProtocolKind,
    WebSocketFrameRecord,
)
from .redact import redact_capsule
from .stability import (
    ReplayObservation,
    StabilityPolicy,
    StabilityReport,
    analyze_stability,
)


class StabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observations: list[ReplayObservation]
    policy: StabilityPolicy = Field(default_factory=StabilityPolicy)


class DifferentialRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    samples: list[ExperimentSample]
    policy: DifferentialDesignPolicy = Field(default_factory=DifferentialDesignPolicy)
    stability_by_role: dict[ControlRole, StabilityReport] = Field(default_factory=dict)


class ProtocolValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ProtocolKind
    records: list[dict[str, Any]]


@contextmanager
def _capsule_root(raw_path: str) -> Iterator[Path]:
    path = Path(raw_path).expanduser().resolve()
    if path.is_dir() and (path / "capsule.json").is_file():
        yield path
        return
    if path.suffix == ".rcap" and path.is_file():
        with tempfile.TemporaryDirectory() as temporary:
            yield safe_extract(path, Path(temporary))
        return
    raise HTTPException(
        400,
        "path must point to an unpacked capsule directory or existing .rcap",
    )


def _timeline(root: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for path in sorted((root / "requests").glob("*.json")):
        request_record = RequestRecord.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        events.append(
            {
                "observed_at": request_record.observed_at,
                "type": "request",
                "id": request_record.request_id,
                "method": request_record.method,
                "url": request_record.url,
            }
        )
    for path in sorted((root / "responses").glob("*.json")):
        response_record = ResponseRecord.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        events.append(
            {
                "observed_at": response_record.observed_at,
                "type": "response",
                "id": response_record.response_id,
                "request_id": response_record.request_id,
                "status": response_record.status_code,
            }
        )
    events.sort(key=lambda item: str(item["observed_at"]))
    return events


def create_app() -> FastAPI:
    app = FastAPI(
        title="ReproSec Local API",
        version=__version__,
        redoc_url=None,
    )

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    web_root = Path(__file__).with_name("webdist")
    if (web_root / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=web_root / "assets"),
            name="assets",
        )

    @app.get("/", include_in_schema=False)
    async def web_index():
        index = web_root / "index.html"
        if index.is_file():
            return FileResponse(index)
        return JSONResponse(
            status_code=503,
            content={"error": "Web UI assets are not installed"},
        )

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/v1/capabilities")
    async def capabilities() -> dict[str, object]:
        return {
            "schema_version": "0.3",
            "implemented": [
                "har_import",
                "raw_http_import",
                "curl_import",
                "structured_redaction",
                "deterministic_pack_verify",
                "signed_manifests",
                "safe_replay",
                "streaming_response_limits",
                "deterministic_extractors",
                "semantic_json_diff",
                "timeline",
                "evidence_lineage",
                "rcap_0_3_multi_actor_sessions",
                "authorized_http_capture",
                "browser_event_recording",
                "workflow_compiler",
                "semantic_diff_v2",
                "burp_zap_import",
                "public_conformance_suite",
                "replay_stability",
                "differential_control_design",
                "passive_websocket_records",
                "passive_grpc_records",
                "passive_graphql_records",
            ],
            "ai_required": False,
            "cloud_uploads_default": False,
            "protocol_records_execute": False,
        }

    @app.get("/api/v1/verify")
    async def verify(path: str) -> dict[str, object]:
        archive = Path(path).expanduser().resolve()
        if archive.suffix != ".rcap" or not archive.is_file():
            raise HTTPException(400, "path must point to an existing .rcap file")
        errors = verify_archive(archive)
        return {"valid": not errors, "errors": errors}

    @app.get("/api/v1/workspace/inspect")
    async def workspace_inspect(path: str) -> dict[str, object]:
        with _capsule_root(path) as root:
            metadata = dict(
                CapsuleMetadata.model_validate_json(
                    (root / "capsule.json").read_text(encoding="utf-8")
                ).model_dump(mode="json")
            )
            metadata["counts"] = {
                name: len(list((root / name).glob("*.json")))
                for name in (
                    "requests",
                    "responses",
                    "workflow",
                    "assertions",
                    "extractors",
                )
            }
            return metadata

    @app.get("/api/v1/workspace/redaction-preview")
    async def redaction_preview(path: str) -> dict[str, object]:
        with _capsule_root(path) as root:
            preview = redact_capsule(root, apply=False)
            return {
                "files_scanned": preview.files_scanned,
                "files_changed": preview.files_changed,
                "detections": preview.detections,
                "applied": False,
            }

    @app.get("/api/v1/workspace/timeline")
    async def workspace_timeline(path: str) -> list[dict[str, object]]:
        with _capsule_root(path) as root:
            return _timeline(root)

    @app.post("/api/v1/precision/stability")
    async def precision_stability(request: StabilityRequest) -> dict[str, object]:
        report = analyze_stability(request.observations, request.policy)
        return report.model_dump(mode="json")

    @app.post("/api/v1/precision/differential-check")
    async def precision_differential(
        request: DifferentialRequest,
    ) -> dict[str, object]:
        report = assess_differential_design(
            request.samples,
            policy=request.policy,
            stability_by_role=request.stability_by_role,
        )
        return report.model_dump(mode="json")

    @app.post("/api/v1/protocol/validate")
    async def protocol_validate(
        request: ProtocolValidationRequest,
    ) -> dict[str, object]:
        model = {
            ProtocolKind.WEBSOCKET: WebSocketFrameRecord,
            ProtocolKind.GRPC: GrpcMessageRecord,
            ProtocolKind.GRAPHQL: GraphQLOperationRecord,
        }[request.kind]
        records = [model.model_validate(item) for item in request.records]
        return {
            "protocol": request.kind.value,
            "records": len(records),
            "record_ids": [item.record_id for item in records],
            "passive_only": True,
            "executed": False,
        }

    return app
