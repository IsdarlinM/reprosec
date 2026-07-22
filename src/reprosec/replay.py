from __future__ import annotations

import base64
import hashlib
import json
import re
import socket
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx

from sric.action_classification import classify_http_action
from sric.audit import AuditLogger
from sric.models import ActionProposal, OperationMode
from sric.policy import PolicyEngine
from sric.rate_limit import RateLimiter, RateLimitPolicy
from sric.scope import ScopeEngine
from sric.redaction import redact_body, redact_text

from . import __version__
from .models import Header, NetworkObservation, RequestRecord, ResponseRecord
from .security import resolve_ips, validate_external_url
from .transport import PinnedHTTPTransport

_VARIABLE = re.compile(r"\$\{\{([A-Za-z0-9_.-]+)\}\}")


class ReplayError(RuntimeError):
    def __init__(self, code: str, message: str, *, target: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.target = target


class ReplayDeniedError(ReplayError, PermissionError):
    pass


@dataclass(frozen=True)
class ReplayResult:
    response: ResponseRecord
    redirects: list[str]


def _bind(value: str | None, bindings: Mapping[str, str]) -> str | None:
    if value is None:
        return None

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in bindings:
            raise ReplayError(
                "E_REPLAY_VARIABLE_001",
                f"required variable {name} is unresolved; bind it explicitly before replay",
            )
        return bindings[name]

    return _VARIABLE.sub(replace, value)


def _bind_url(value: str, bindings: Mapping[str, str]) -> str:
    parsed = urlsplit(value)
    path = _bind(parsed.path, bindings) or parsed.path
    query_items: list[tuple[str, str]] = []
    for key, raw in parse_qsl(parsed.query, keep_blank_values=True):
        query_items.append((_bind(key, bindings) or "", _bind(raw, bindings) or ""))
    query = urlencode(query_items, doseq=True)
    return urlunsplit((parsed.scheme, parsed.netloc, path, query, ""))


def _bind_body(value: str | None, bindings: Mapping[str, str], media_type: str | None) -> str | None:
    if value is None:
        return None
    ctype = (media_type or "").split(";", 1)[0].strip().lower()
    if ctype in {"application/json", "application/ld+json"} or value.lstrip().startswith(("{", "[")):
        try:
            obj = json.loads(value)
        except json.JSONDecodeError:
            return _bind(value, bindings)

        def replace(node: object) -> object:
            if isinstance(node, dict):
                return {key: replace(child) for key, child in node.items()}
            if isinstance(node, list):
                return [replace(child) for child in node]
            if isinstance(node, str):
                return _bind(node, bindings)
            return node

        return json.dumps(replace(obj), separators=(",", ":"), ensure_ascii=False)
    if ctype == "application/x-www-form-urlencoded":
        items = [
            (_bind(key, bindings) or "", _bind(raw, bindings) or "")
            for key, raw in parse_qsl(value, keep_blank_values=True)
        ]
        return urlencode(items, doseq=True)
    return _bind(value, bindings)


def _connection_info(response: httpx.Response) -> tuple[str | None, str | None, str | None]:
    stream = response.extensions.get("network_stream")
    if stream is None or not hasattr(stream, "get_extra_info"):
        return None, None, None
    peer: str | None = None
    for key in ("server_addr", "peername"):
        try:
            value = stream.get_extra_info(key)
        except Exception:
            value = None
        if isinstance(value, tuple) and value:
            peer = str(value[0])
            break
        if isinstance(value, str):
            peer = value
            break
    tls_version: str | None = None
    alpn: str | None = None
    try:
        ssl_object = stream.get_extra_info("ssl_object")
        if ssl_object is not None:
            if hasattr(ssl_object, "version"):
                tls_version = ssl_object.version()
            if hasattr(ssl_object, "selected_alpn_protocol"):
                alpn = ssl_object.selected_alpn_protocol()
    except Exception:
        pass
    if peer is None:
        try:
            sock = stream.get_extra_info("socket")
            if sock is not None:
                raw_peer = sock.getpeername()
                if isinstance(raw_peer, tuple) and raw_peer:
                    peer = str(raw_peer[0])
        except Exception:
            pass
    return peer, tls_version, alpn


def _is_textual(media_type: str | None) -> bool:
    value = (media_type or "").lower()
    return value.startswith("text/") or any(
        token in value for token in ("json", "xml", "javascript", "graphql", "yaml")
    )


class Replayer:
    def __init__(
        self,
        scope: ScopeEngine,
        policy: PolicyEngine | None = None,
        *,
        timeout: float = 10.0,
        max_redirects: int = 5,
        follow_redirects: bool = False,
        rate_limiter: RateLimiter | None = None,
        proxy: str | None = None,
        allow_proxy_routing: bool = False,
        max_store_bytes: int = 10 * 1024 * 1024,
        max_download_bytes: int = 50 * 1024 * 1024,
        strict_peer_verification: bool = True,
        mode: OperationMode = OperationMode.VALIDATE,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.scope = scope
        self.policy = policy or PolicyEngine()
        self.rate_limiter = rate_limiter or RateLimiter(RateLimitPolicy())
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.follow_redirects = follow_redirects
        self.proxy = proxy
        self.allow_proxy_routing = allow_proxy_routing
        self.max_store_bytes = max_store_bytes
        self.max_download_bytes = max_download_bytes
        self.strict_peer_verification = strict_peer_verification
        self.mode = mode
        self.audit_logger = audit_logger
        if proxy:
            validate_external_url(proxy)
            if not allow_proxy_routing:
                raise ReplayDeniedError(
                    "E_REPLAY_PROXY_001",
                    "explicit proxy routing requires explicit approval because the proxy may resolve/connect to the target independently",
                    target=proxy,
                )

    def replay(
        self,
        req: RequestRecord,
        *,
        human_approved: bool = False,
        bindings: Mapping[str, str] | None = None,
    ) -> ReplayResult:
        bindings = bindings or {}
        method = req.method.upper()
        current = _bind_url(req.url, bindings)
        redirects: list[str] = []
        headers = [(h.name, _bind(h.value, bindings) or "") for h in req.headers]
        media_type = req.media_type
        if media_type is None:
            for name, value in headers:
                if name.lower() == "content-type":
                    media_type = value
                    break
        body = _bind_body(req.body, bindings, media_type)

        for hop in range(self.max_redirects + 1):
            action_class = classify_http_action(method, current)
            pre_dns = self.scope.evaluate(current, method)
            if not pre_dns.allowed:
                raise ReplayDeniedError(
                    "E_REPLAY_SCOPE_001",
                    f"scope denied replay: {pre_dns.reason} ({pre_dns.matched_rule})",
                    target=current,
                )
            try:
                ips = resolve_ips(current)
            except socket.gaierror as exc:
                raise ReplayError(
                    "E_REPLAY_DNS_001",
                    f"DNS resolution failed for {urlsplit(current).hostname}; no HTTP request was sent",
                    target=current,
                ) from exc
            sd = self.scope.evaluate(current, method, resolved_ips=ips)
            if not sd.allowed:
                raise ReplayDeniedError(
                    "E_REPLAY_SCOPE_002",
                    f"scope denied resolved target: {sd.reason} ({sd.matched_rule})",
                    target=current,
                )

            action = ActionProposal(
                action_id=f"REPLAY-{req.request_id}-HOP-{hop}",
                actor="reprosec-user",
                method=method,
                target=current,
                action_class=action_class,
                mode=self.mode,
            )
            preflight = self.policy.preflight(action)
            if not preflight.allowed:
                raise ReplayDeniedError(
                    "E_REPLAY_POLICY_001",
                    f"policy denied replay: {preflight.matched_rule}",
                    target=current,
                )

            host = urlsplit(current).hostname or "unknown"
            self.rate_limiter.acquire(host)

            decision = self.policy.decide(action, human_approved=human_approved)
            if not decision.allowed:
                if self.audit_logger:
                    self.audit_logger.write(
                        user="reprosec-user", action=f"{method} replay", target=current,
                        policy_decision=decision.decision, result="denied", tool_version=__version__,
                        metadata={"action_class": action_class.value, "rule": decision.matched_rule, "mode": self.mode.value},
                    )
                raise ReplayDeniedError(
                    "E_REPLAY_APPROVAL_001",
                    f"human approval required: {decision.matched_rule}",
                    target=current,
                )
            if self.audit_logger:
                self.audit_logger.write(
                    user="reprosec-user", action=f"{method} replay", target=current,
                    policy_decision=decision.decision, result="approved_for_execution", tool_version=__version__,
                    metadata={"action_class": action_class.value, "rule": decision.matched_rule, "mode": self.mode.value},
                )

            if self.proxy:
                client = httpx.Client(
                    timeout=self.timeout,
                    follow_redirects=False,
                    trust_env=False,
                    proxy=self.proxy,
                )
            else:
                client = httpx.Client(
                    timeout=self.timeout,
                    follow_redirects=False,
                    trust_env=False,
                    transport=PinnedHTTPTransport(host, ips, http2=True),
                )

            try:
                with client:
                    with client.stream(method, current, headers=headers, content=body) as r:
                        peer, tls_version, alpn = _connection_info(r)
                        target_peer_verified = False
                        if not self.proxy and self.strict_peer_verification:
                            if peer is None:
                                raise ReplayError(
                                    "E_REPLAY_PEER_001",
                                    "connected peer address could not be verified; replay stopped fail-closed",
                                    target=current,
                                )
                            peer_scope = self.scope.evaluate(current, method, resolved_ips=[peer])
                            if not peer_scope.allowed:
                                raise ReplayDeniedError(
                                    "E_REPLAY_PEER_002",
                                    f"connected peer violates scope/network policy: {peer_scope.reason}",
                                    target=current,
                                )
                            if peer not in ips:
                                raise ReplayDeniedError(
                                    "E_REPLAY_PEER_003",
                                    "connected peer differs from the prevalidated/pinned DNS set",
                                    target=current,
                                )
                            target_peer_verified = True

                        if r.is_redirect and self.follow_redirects:
                            if hop >= self.max_redirects:
                                raise ReplayError(
                                    "E_REPLAY_REDIRECT_001",
                                    "maximum redirects exceeded",
                                    target=current,
                                )
                            location = r.headers.get("location")
                            if not location:
                                raise ReplayError(
                                    "E_REPLAY_REDIRECT_002",
                                    "redirect response did not include a Location header",
                                    target=current,
                                )
                            nxt = urljoin(current, location)
                            rd = self.scope.evaluate_redirect(current, nxt, method)
                            if not rd.allowed:
                                raise ReplayDeniedError(
                                    "E_REPLAY_SCOPE_003",
                                    f"redirect left scope: {rd.reason}",
                                    target=nxt,
                                )
                            redirects.append(nxt)
                            current = nxt
                            continue

                        declared = r.headers.get("content-length")
                        if declared and declared.isdigit() and int(declared) > self.max_download_bytes:
                            raise ReplayError(
                                "E_REPLAY_SIZE_001",
                                f"response Content-Length exceeds max_download_bytes={self.max_download_bytes}",
                                target=current,
                            )
                        digest = hashlib.sha256()
                        stored = bytearray()
                        total = 0
                        for chunk in r.iter_bytes():
                            total += len(chunk)
                            if total > self.max_download_bytes:
                                raise ReplayError(
                                    "E_REPLAY_SIZE_002",
                                    f"response exceeded max_download_bytes={self.max_download_bytes}",
                                    target=current,
                                )
                            digest.update(chunk)
                            if len(stored) < self.max_store_bytes:
                                remaining = self.max_store_bytes - len(stored)
                                stored.extend(chunk[:remaining])
                        media_type = r.headers.get("content-type")
                        body_text = None
                        body_b64 = None
                        redacted = False
                        if _is_textual(media_type):
                            body_text = bytes(stored).decode(r.encoding or "utf-8", errors="replace")
                            rr = redact_body(body_text, media_type)
                            body_text = rr.text
                            redacted = bool(rr.detected)
                        elif stored:
                            body_b64 = base64.b64encode(bytes(stored)).decode("ascii")
                        response_headers: list[Header] = []
                        for key, value in r.headers.multi_items():
                            rr = redact_text(f"{key}: {value}")
                            name, _, redacted_value = rr.text.partition(":")
                            redacted |= bool(rr.detected)
                            response_headers.append(
                                Header(name=name.strip(), value=redacted_value.strip())
                            )
                        response = ResponseRecord(
                            request_id=req.request_id,
                            status_code=r.status_code,
                            headers=response_headers,
                            body=body_text,
                            body_base64=body_b64,
                            body_sha256=digest.hexdigest(),
                            body_size_bytes=total,
                            body_truncated=total > len(stored),
                            media_type=media_type,
                            redacted=redacted,
                            network=NetworkObservation(
                                resolved_ips=ips,
                                peer_ip=peer,
                                http_version=r.http_version,
                                tls_version=tls_version,
                                alpn=alpn,
                                proxy_url=self.proxy,
                                target_peer_verified=target_peer_verified,
                            ),
                        )
                        if self.audit_logger:
                            self.audit_logger.write(
                                user="reprosec-user", action=f"{method} replay", target=current,
                                policy_decision=decision.decision, result=f"http_status_{r.status_code}", tool_version=__version__,
                                metadata={"response_id": response.response_id, "target_peer_verified": target_peer_verified},
                            )
                        return ReplayResult(response=response, redirects=redirects)
            except ReplayError:
                raise
            except httpx.ConnectError as exc:
                message = str(exc)
                code = (
                    "E_REPLAY_TLS_001"
                    if any(x in message.lower() for x in ("ssl", "tls", "certificate"))
                    else "E_REPLAY_NETWORK_001"
                )
                raise ReplayError(code, f"connection failed: {message}", target=current) from exc
            except httpx.TimeoutException as exc:
                raise ReplayError(
                    "E_REPLAY_TIMEOUT_001", "HTTP replay timed out", target=current
                ) from exc
            except httpx.NetworkError as exc:
                raise ReplayError(
                    "E_REPLAY_NETWORK_001", f"network replay failed: {exc}", target=current
                ) from exc

        raise ReplayError(
            "E_REPLAY_INTERNAL_001", "replay did not produce a terminal response", target=current
        )
