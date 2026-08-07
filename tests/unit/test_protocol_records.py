import hashlib

import pytest

from reprosec.protocols import (
    Direction,
    GraphQLOperationKind,
    GraphQLOperationRecord,
    GrpcMessageRecord,
    ProtocolKind,
    WebSocketFrameRecord,
    WebSocketOpcode,
)


HASH = hashlib.sha256(b"payload").hexdigest()


def test_websocket_frame_preserves_bounded_evidence_metadata() -> None:
    record = WebSocketFrameRecord(
        record_id="WS-1",
        connection_id="CONN-1",
        direction=Direction.SERVER_TO_CLIENT,
        evidence_ids=["E-1"],
        provenance_source="capture",
        payload_sha256=HASH,
        payload_size=100,
        retained_size=20,
        truncated=True,
        frame_index=0,
        opcode=WebSocketOpcode.TEXT,
    )

    assert record.protocol is ProtocolKind.WEBSOCKET
    assert record.truncated is True


def test_grpc_metadata_stores_keys_not_secret_values() -> None:
    record = GrpcMessageRecord(
        record_id="G-1",
        connection_id="CONN-1",
        direction=Direction.CLIENT_TO_SERVER,
        evidence_ids=["E-1"],
        provenance_source="import",
        service="demo.Service",
        method="Get",
        stream_index=0,
        metadata_keys=["authorization", "x-request-id"],
    )

    assert record.protocol is ProtocolKind.GRPC
    assert record.metadata_keys == ["authorization", "x-request-id"]


def test_graphql_subscription_event_is_typed() -> None:
    record = GraphQLOperationRecord(
        record_id="Q-1",
        connection_id="CONN-1",
        direction=Direction.SERVER_TO_CLIENT,
        evidence_ids=["E-1"],
        provenance_source="capture",
        operation_kind=GraphQLOperationKind.SUBSCRIPTION,
        operation_name="Updates",
        document_sha256=HASH,
        subscription_event_index=2,
    )

    assert record.protocol is ProtocolKind.GRAPHQL
    assert record.subscription_event_index == 2


def test_non_subscription_cannot_have_event_index() -> None:
    with pytest.raises(ValueError, match="requires a SUBSCRIPTION"):
        GraphQLOperationRecord(
            record_id="Q-2",
            connection_id="CONN-1",
            direction=Direction.SERVER_TO_CLIENT,
            evidence_ids=["E-1"],
            provenance_source="capture",
            operation_kind=GraphQLOperationKind.QUERY,
            subscription_event_index=1,
        )


def test_protocol_records_require_evidence() -> None:
    with pytest.raises(ValueError, match="require evidence_ids"):
        WebSocketFrameRecord(
            record_id="WS-X",
            connection_id="CONN-1",
            direction=Direction.CLIENT_TO_SERVER,
            provenance_source="capture",
            frame_index=0,
            opcode=WebSocketOpcode.PING,
        )


def test_invalid_retention_metadata_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        WebSocketFrameRecord(
            record_id="WS-X",
            connection_id="CONN-1",
            direction=Direction.CLIENT_TO_SERVER,
            evidence_ids=["E-1"],
            provenance_source="capture",
            payload_size=10,
            retained_size=11,
            frame_index=0,
            opcode=WebSocketOpcode.BINARY,
        )
