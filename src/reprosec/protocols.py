from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProtocolKind(StrEnum):
    WEBSOCKET = "WEBSOCKET"
    GRPC = "GRPC"
    GRAPHQL = "GRAPHQL"


class Direction(StrEnum):
    CLIENT_TO_SERVER = "CLIENT_TO_SERVER"
    SERVER_TO_CLIENT = "SERVER_TO_CLIENT"


class WebSocketOpcode(StrEnum):
    CONTINUATION = "CONTINUATION"
    TEXT = "TEXT"
    BINARY = "BINARY"
    CLOSE = "CLOSE"
    PING = "PING"
    PONG = "PONG"
    UNKNOWN = "UNKNOWN"


class GraphQLOperationKind(StrEnum):
    QUERY = "QUERY"
    MUTATION = "MUTATION"
    SUBSCRIPTION = "SUBSCRIPTION"
    UNKNOWN = "UNKNOWN"


class ProtocolEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    protocol: ProtocolKind
    connection_id: str
    direction: Direction
    observed_at: datetime = Field(default_factory=utcnow)
    evidence_ids: list[str] = Field(default_factory=list)
    provenance_source: str
    payload_sha256: str | None = None
    payload_size: int | None = Field(default=None, ge=0)
    retained_size: int = Field(default=0, ge=0)
    truncated: bool = False
    redacted: bool = True
    metadata: dict[str, str | int | bool | None] = Field(default_factory=dict)

    @field_validator("payload_sha256")
    @classmethod
    def validate_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) != 64:
            raise ValueError("payload_sha256 must be a 64-character SHA-256 hex digest")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("payload_sha256 must be hexadecimal") from exc
        return value.lower()

    @model_validator(mode="after")
    def evidence_and_retention_semantics(self) -> "ProtocolEvidenceRecord":
        if not self.evidence_ids:
            raise ValueError("protocol observations require evidence_ids")
        if self.payload_size is not None and self.retained_size > self.payload_size:
            raise ValueError("retained_size cannot exceed payload_size")
        if self.truncated and self.payload_size is not None and self.retained_size >= self.payload_size:
            raise ValueError("truncated records must retain less than the observed payload size")
        return self


class WebSocketFrameRecord(ProtocolEvidenceRecord):
    protocol: ProtocolKind = ProtocolKind.WEBSOCKET
    frame_index: int = Field(ge=0)
    opcode: WebSocketOpcode
    final_fragment: bool = True
    masked: bool | None = None
    close_code: int | None = Field(default=None, ge=0, le=4999)
    close_reason_redacted: str | None = None


class GrpcMessageRecord(ProtocolEvidenceRecord):
    protocol: ProtocolKind = ProtocolKind.GRPC
    service: str
    method: str
    stream_index: int = Field(ge=0)
    compressed: bool | None = None
    grpc_status: int | None = Field(default=None, ge=0, le=16)
    grpc_message_redacted: str | None = None
    metadata_keys: list[str] = Field(default_factory=list)
    trailers: bool = False


class GraphQLOperationRecord(ProtocolEvidenceRecord):
    protocol: ProtocolKind = ProtocolKind.GRAPHQL
    operation_kind: GraphQLOperationKind
    operation_name: str | None = None
    document_sha256: str | None = None
    variables_sha256: str | None = None
    response_path: str | None = None
    error_codes: list[str] = Field(default_factory=list)
    subscription_event_index: int | None = Field(default=None, ge=0)

    @field_validator("document_sha256", "variables_sha256")
    @classmethod
    def validate_optional_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) != 64:
            raise ValueError("GraphQL hashes must be 64-character SHA-256 hex digests")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("GraphQL hashes must be hexadecimal") from exc
        return value.lower()

    @model_validator(mode="after")
    def subscription_event_semantics(self) -> "GraphQLOperationRecord":
        if (
            self.subscription_event_index is not None
            and self.operation_kind is not GraphQLOperationKind.SUBSCRIPTION
        ):
            raise ValueError("subscription_event_index requires a SUBSCRIPTION operation")
        return self
