from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from sric.action_classification import classify_http_action
from sric.models import ActionProposal, OperationMode
from sric.policy import PolicyEngine
from sric.rate_limit import RateLimiter, RateLimitPolicy
from sric.scope import ScopeEngine

from .capsule import add_capture_event, add_request, add_response, add_workflow_step
from .models import CaptureEvent, Header, NetworkObservation, RequestRecord, ResponseRecord, WorkflowStep
from sric.redaction import redact_text
from .security import resolve_ips
from .transport import PinnedHTTPTransport

import httpx


def _redact_header_pairs(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out=[]
    for key,value in items:
        rr=redact_text(f"{key}: {value}")
        name,_,redacted=rr.text.partition(":")
        out.append((name.strip(),redacted.strip()))
    return out


@dataclass(frozen=True)
class CaptureLimits:
    max_store_bytes: int = 10 * 1024 * 1024
    max_download_bytes: int = 50 * 1024 * 1024


class CaptureDeniedError(PermissionError):
    pass


class CaptureRecorder:
    """Evidence recorder for authorized/local HTTP capture.

    Capture is evidence acquisition only. It never marks a claim VALIDATED. Requests are gated by
    Scope/Policy/RateLimit/Approval before the executor is called.
    """

    def __init__(
        self,
        capsule: Path,
        scope: ScopeEngine,
        *,
        policy: PolicyEngine | None = None,
        rate_limiter: RateLimiter | None = None,
        limits: CaptureLimits | None = None,
    ) -> None:
        self.capsule = capsule
        self.scope = scope
        self.policy = policy or PolicyEngine()
        self.rate_limiter = rate_limiter or RateLimiter(RateLimitPolicy())
        self.limits = limits or CaptureLimits()

    def capture(
        self,
        method: str,
        url: str,
        *,
        headers: list[tuple[str, str]] | None = None,
        body: bytes | None = None,
        actor_id: str | None = None,
        session_id: str | None = None,
        approved: bool = False,
    ) -> tuple[RequestRecord, ResponseRecord]:
        method = method.upper()
        pre = self.scope.evaluate(url, method)
        if not pre.allowed:
            raise CaptureDeniedError(f"scope denied capture: {pre.reason}")
        ips = resolve_ips(url)
        scoped = self.scope.evaluate(url, method, resolved_ips=ips)
        if not scoped.allowed:
            raise CaptureDeniedError(f"resolved target denied: {scoped.reason}")
        action = ActionProposal(
            action_id=f"CAP-{time.time_ns()}", actor=actor_id or "reprosec-user", method=method,
            target=url, action_class=classify_http_action(method, url), mode=OperationMode.OBSERVE,
        )
        preflight = self.policy.preflight(action)
        if not preflight.allowed:
            raise CaptureDeniedError(f"policy denied capture: {preflight.matched_rule}")
        decision = self.policy.decide(action, human_approved=approved)
        if not decision.allowed:
            raise CaptureDeniedError(f"approval required: {decision.matched_rule}")
        host = urlsplit(url).hostname or "unknown"
        self.rate_limiter.acquire(host)
        started = time.time()
        redacted_headers = _redact_header_pairs(headers or [])
        content_type = next((v for k,v in headers or [] if k.lower()=="content-type"), None)
        gql_name, gql_type = detect_graphql(body, content_type)
        req = RequestRecord(
            method=method, url=url, headers=[Header(name=k, value=v) for k, v in redacted_headers],
            body=(body.decode("utf-8", errors="replace") if body else None), body_size_bytes=len(body or b""),
            body_sha256=hashlib.sha256(body or b"").hexdigest(), source="capture_proxy",
            actor_id=actor_id, session_id=session_id, redacted=True, media_type=content_type,
            graphql_operation=gql_name, graphql_operation_type=gql_type,
        )
        add_request(self.capsule, req)
        add_workflow_step(self.capsule, WorkflowStep(actor=actor_id or "Actor", actor_id=actor_id, session_id=session_id, request_id=req.request_id))
        transport = PinnedHTTPTransport(host, ips, http2=True)
        with httpx.Client(transport=transport, follow_redirects=False, trust_env=False, timeout=30) as client:
            with client.stream(method, url, headers=headers, content=body) as response:
                data = bytearray(); total = 0; digest = hashlib.sha256()
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > self.limits.max_download_bytes:
                        raise ValueError("capture response exceeds max_download_bytes")
                    digest.update(chunk)
                    if len(data) < self.limits.max_store_bytes:
                        data.extend(chunk[: self.limits.max_store_bytes - len(data)])
                media = response.headers.get("content-type")
                text = bytes(data).decode(response.encoding or "utf-8", errors="replace") if (media or "").startswith("text/") or "json" in (media or "") else None
                res = ResponseRecord(
                    request_id=req.request_id, status_code=response.status_code,
                    headers=[Header(name=k, value=v) for k, v in _redact_header_pairs(list(response.headers.multi_items()))],
                    body=text, body_sha256=digest.hexdigest(), body_size_bytes=total,
                    body_truncated=total > len(data), media_type=media, redacted=True,
                    network=NetworkObservation(resolved_ips=ips, http_version=response.http_version,
                        connect_started_at=str(started), completed_at=str(time.time()), duration_ms=(time.time()-started)*1000),
                )
        add_response(self.capsule, res)
        add_capture_event(self.capsule, CaptureEvent(event_type="http", actor_id=actor_id, session_id=session_id, data={"request_id": req.request_id, "response_id": res.response_id, "capture_is_validation": False}))
        return req, res

    def record_tls_tunnel(self, host: str, port: int, *, actor_id: str | None = None, session_id: str | None = None) -> CaptureEvent:
        event = CaptureEvent(event_type="tls_tunnel", actor_id=actor_id, session_id=session_id, data={"host": host, "port": port, "decrypted": False, "note": "CONNECT/TLS metadata only; no silent MITM"})
        add_capture_event(self.capsule, event)
        return event


def detect_graphql(body: bytes | None, content_type: str | None) -> tuple[str | None, str | None]:
    if not body:
        return None, None
    text=body.decode("utf-8",errors="replace").strip()
    query=None
    if "json" in (content_type or "").casefold():
        try:
            obj=json.loads(text)
            if isinstance(obj,dict) and isinstance(obj.get("query"),str): query=obj["query"]
        except json.JSONDecodeError: pass
    elif "graphql" in (content_type or "").casefold(): query=text
    if not query:return None,None
    stripped=query.lstrip();op="query"
    for candidate in ("mutation","subscription","query"):
        if stripped.startswith(candidate):op=candidate;break
    name=None
    parts=stripped.replace("{"," { ").split()
    if parts and parts[0] in {"query","mutation","subscription"} and len(parts)>1 and parts[1]!="{":name=parts[1].split("(",1)[0]
    return name,op


class LocalCaptureProxy:
    """Loopback HTTP forward proxy for explicit research capture.

    Plain HTTP requests are forwarded through CaptureRecorder safety gates. CONNECT is never silently
    intercepted: the proxy records TLS tunnel metadata and returns 501, requiring an explicitly
    configured external TLS interception workflow if the researcher needs decrypted HTTPS capture.
    """
    def __init__(self,capsule:Path,scope:ScopeEngine,*,host:str="127.0.0.1",port:int=8787,approve_mutating:bool=False)->None:
        if host not in {"127.0.0.1","localhost","::1"}:raise ValueError("capture proxy binds loopback only")
        self.capsule=capsule;self.scope=scope;self.host=host;self.port=port;self.approve_mutating=approve_mutating
    def serve(self)->None:
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        outer=self
        class Handler(BaseHTTPRequestHandler):
            protocol_version="HTTP/1.1"
            def _handle(self)->None:
                if self.command=="CONNECT":
                    connect_host,_,port_text=self.path.partition(":");port=int(port_text or 443);CaptureRecorder(outer.capsule,outer.scope).record_tls_tunnel(connect_host,port);response_body=b"CONNECT interception disabled; TLS tunnel metadata recorded only.\n";self.send_response(501);self.send_header("Content-Type","text/plain");self.send_header("Content-Length",str(len(response_body)));self.end_headers();self.wfile.write(response_body);return
                url=self.path
                if not url.startswith(("http://","https://")):
                    header_host=self.headers.get("Host")
                    if not header_host:self.send_error(400,"Host required");return
                    url=f"http://{header_host}{self.path}"
                length=int(self.headers.get("Content-Length","0") or 0)
                if length>10*1024*1024:self.send_error(413,"request body too large");return
                body=self.rfile.read(length) if length else None
                headers=[(k,v) for k,v in self.headers.items() if k.lower() not in {"proxy-connection","connection","content-length"}]
                try:
                    req,res=CaptureRecorder(outer.capsule,outer.scope).capture(self.command,url,headers=headers,body=body,approved=outer.approve_mutating)
                except Exception as exc:
                    msg=f"Capture denied/failed: {exc}".encode();self.send_response(502);self.send_header("Content-Length",str(len(msg)));self.end_headers();self.wfile.write(msg);return
                payload=(res.body or "").encode("utf-8")
                self.send_response(res.status_code)
                for h in res.headers:
                    if h.name.lower() not in {"content-length","transfer-encoding","connection","content-encoding"}:self.send_header(h.name,h.value)
                self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload)
            do_GET=_handle;do_POST=_handle;do_PUT=_handle;do_PATCH=_handle;do_DELETE=_handle;do_OPTIONS=_handle;do_HEAD=_handle;do_CONNECT=_handle
            def log_message(self,fmt:str,*args:object)->None:return
        ThreadingHTTPServer((self.host,self.port),Handler).serve_forever()
