from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Header(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    value: str


class NetworkObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolved_ips: list[str] = Field(default_factory=list)
    peer_ip: str | None = None
    http_version: str | None = None
    tls_version: str | None = None
    alpn: str | None = None
    proxy_url: str | None = None
    target_peer_verified: bool = False
    connect_started_at: str | None = None
    first_byte_at: str | None = None
    completed_at: str | None = None
    duration_ms: float | None = Field(default=None, ge=0)


class SecretReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    secret_ref: str
    purpose: str
    scope: str = "session"


class ActorRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_id: str = Field(default_factory=lambda: f"ACT-{uuid4().hex[:12].upper()}")
    label: str
    actor_type: str = "user"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(default_factory=lambda: f"SES-{uuid4().hex[:12].upper()}")
    actor_id: str
    label: str
    created_at: str = Field(default_factory=now_iso)
    ended_at: str | None = None
    secret_references: list[SecretReference] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequestRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(default_factory=lambda: f"REQ-{uuid4().hex[:12].upper()}")
    method: str
    url: str
    headers: list[Header] = Field(default_factory=list)
    body: str | None = None
    body_base64: str | None = None
    body_sha256: str | None = None
    body_size_bytes: int | None = Field(default=None, ge=0)
    media_type: str | None = None
    observed_at: str = Field(default_factory=now_iso)
    source: str = "user_input"
    redacted: bool = False
    actor_id: str | None = None
    session_id: str | None = None
    graphql_operation: str | None = None
    graphql_operation_type: str | None = None
    import_metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_id: str = Field(default_factory=lambda: f"RES-{uuid4().hex[:12].upper()}")
    request_id: str
    status_code: int = Field(ge=100, le=599)
    headers: list[Header] = Field(default_factory=list)
    body: str | None = None
    body_base64: str | None = None
    body_sha256: str | None = None
    body_size_bytes: int | None = Field(default=None, ge=0)
    body_truncated: bool = False
    media_type: str | None = None
    observed_at: str = Field(default_factory=now_iso)
    redacted: bool = False
    network: NetworkObservation | None = None
    redirect_chain: list[str] = Field(default_factory=list)


AssertionKind = Literal["status_code", "status_in", "header_exists", "header_equals", "body_contains", "body_not_contains", "body_regex", "jsonpath_exists", "jsonpath_equals"]


class AssertionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assertion_id: str = Field(default_factory=lambda: f"AST-{uuid4().hex[:12].upper()}")
    request_id: str
    kind: AssertionKind
    expected: str
    selector: str | None = None


ExtractorKind = Literal["header", "cookie", "regex", "jsonpath"]


class ExtractorSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    extractor_id: str = Field(default_factory=lambda: f"EXT-{uuid4().hex[:12].upper()}")
    response_id: str
    name: str
    kind: ExtractorKind
    selector: str
    sensitive: bool = False
    actor_scope: str | None = None


class WorkflowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_id: str = Field(default_factory=lambda: f"STEP-{uuid4().hex[:10].upper()}")
    actor: str
    request_id: str
    actor_id: str | None = None
    session_id: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    state: Literal["OBSERVED", "INFERRED", "HYPOTHESIS", "VALIDATED", "REJECTED", "UNKNOWN"] = "OBSERVED"


class ValidationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    validation_id: str = Field(default_factory=lambda: f"VAL-{uuid4().hex[:12].upper()}")
    claim_id: str | None = None
    request_id: str | None = None
    assertion_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    result: Literal["VALIDATED", "REJECTED", "UNKNOWN"]
    deterministic: bool = True
    observed_at: str = Field(default_factory=now_iso)
    notes: str = ""


class CaptureEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(default_factory=lambda: f"CAP-{uuid4().hex[:12].upper()}")
    event_type: Literal["navigation", "http", "websocket", "storage", "dom_assertion", "tls_tunnel"]
    actor_id: str | None = None
    session_id: str | None = None
    observed_at: str = Field(default_factory=now_iso)
    data: dict[str, Any] = Field(default_factory=dict)
    redacted: bool = True


class CapsuleMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format: Literal["RCAP"] = "RCAP"
    schema_version: str = "0.3"
    capsule_id: str = Field(default_factory=lambda: f"RCAP-{uuid4().hex.upper()}")
    title: str
    created_at: str = Field(default_factory=now_iso)
    created_by: str = "reprosec"
    tool_version: str = "0.5.0"
    deterministic_replay: bool = False
    notes: str = ""
    workspace_id: str | None = None


class ManifestEntry(BaseModel):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class CapsuleManifest(BaseModel):
    format: Literal["RCAP-MANIFEST"] = "RCAP-MANIFEST"
    schema_version: str = "0.3"
    capsule_id: str
    entries: list[ManifestEntry]
