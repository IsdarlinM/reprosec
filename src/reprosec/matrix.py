from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from .models import RequestRecord, ResponseRecord, WorkflowStep


def observed_matrix(root: Path) -> dict[str, object]:
    requests: dict[str, RequestRecord] = {}
    for path in sorted((root / "requests").glob("*.json")):
        request = RequestRecord.model_validate_json(path.read_text(encoding="utf-8"))
        requests[request.request_id] = request
    latest_status: dict[str, int] = {}
    for path in sorted((root / "responses").glob("*.json")):
        response = ResponseRecord.model_validate_json(path.read_text(encoding="utf-8"))
        latest_status[response.request_id] = response.status_code
    rows: dict[str, dict[str, int | str]] = defaultdict(dict)
    operations: set[str] = set()
    for path in sorted((root / "workflow").glob("*.json")):
        step = WorkflowStep.model_validate_json(path.read_text(encoding="utf-8"))
        current_request = requests.get(step.request_id)
        if current_request is None:
            continue
        parsed = urlsplit(current_request.url)
        operation = f"{current_request.method.upper()} {parsed.path or '/'}"
        operations.add(operation)
        rows[step.actor][operation] = latest_status.get(step.request_id, "UNKNOWN")
    ordered_operations = sorted(operations)
    normalized = {
        actor: {operation: values.get(operation, "UNKNOWN") for operation in ordered_operations}
        for actor, values in sorted(rows.items())
    }
    return {
        "kind": "OBSERVED_AUTHORIZATION_EVIDENCE_MATRIX",
        "note": "UNKNOWN means no stored response evidence; it is not a vulnerability.",
        "operations": ordered_operations,
        "actors": normalized,
    }
