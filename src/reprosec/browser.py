from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, cast

from .capsule import add_capture_event
from .models import CaptureEvent

SENSITIVE_KEYS = {"password", "passwd", "authorization", "cookie", "token", "secret"}
BrowserEventType = Literal["navigation", "http", "websocket", "storage", "dom_assertion"]


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("<redacted>" if k.casefold() in SENSITIVE_KEYS else _sanitize(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(x) for x in value]
    return value


class BrowserRecorder:
    """Controlled local recorder for browser-produced event JSON.

    It consumes explicit events from a trusted recorder/export; it does not inject scripts into a
    target and never stores raw password/token fields.
    """
    def __init__(self, capsule: Path) -> None:
        self.capsule = capsule

    def record_event(self, event_type: BrowserEventType, data: dict[str, Any], *, actor_id: str | None = None, session_id: str | None = None) -> CaptureEvent:
        if event_type not in {"navigation", "http", "websocket", "storage", "dom_assertion"}:
            raise ValueError("unsupported browser event type")
        event = CaptureEvent(event_type=event_type, actor_id=actor_id, session_id=session_id, data=_sanitize(data), redacted=True)
        add_capture_event(self.capsule, event)
        return event

    def import_jsonl(self, path: Path, *, actor_id: str | None = None, session_id: str | None = None) -> list[CaptureEvent]:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 50 * 1024 * 1024:
            raise ValueError("browser recording must be a bounded regular file")
        events=[]
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            raw=json.loads(line)
            if not isinstance(raw,dict) or not isinstance(raw.get("type"),str) or not isinstance(raw.get("data",{}),dict):
                raise ValueError("invalid browser recording event")
            event_type = cast(BrowserEventType, raw["type"])
            events.append(self.record_event(event_type,raw.get("data",{}),actor_id=actor_id,session_id=session_id))
        return events


class BrowserRecordingSession:
    """Lifecycle marker for a controlled recorder integration.

    The recorder itself is intentionally transport-agnostic: a browser extension/Playwright adapter may
    POST or export events, while this class records start/stop state and actor/session context locally.
    """
    def __init__(self,capsule:Path)->None:
        self.capsule=capsule;self.state_path=capsule/"environment"/"browser-recorder.json"
    def start(self,*,actor_id:str|None=None,session_id:str|None=None)->dict[str,Any]:
        if self.state_path.exists():
            current=json.loads(self.state_path.read_text())
            if current.get("active"):raise RuntimeError("browser recorder is already active")
        state={"active":True,"actor_id":actor_id,"session_id":session_id,"started_at":__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
        self.state_path.write_text(json.dumps(state,indent=2),encoding="utf-8");return state
    def stop(self)->dict[str,Any]:
        if not self.state_path.is_file():raise RuntimeError("browser recorder has not been started")
        state=cast(dict[str,Any],json.loads(self.state_path.read_text()));state["active"]=False;state["stopped_at"]=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();self.state_path.write_text(json.dumps(state,indent=2),encoding="utf-8");return state
    def status(self)->dict[str,Any]:
        return cast(dict[str,Any],json.loads(self.state_path.read_text())) if self.state_path.is_file() else {"active":False}
