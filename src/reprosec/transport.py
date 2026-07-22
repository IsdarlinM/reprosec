from __future__ import annotations

import socket
import ssl
from collections.abc import Iterable
from typing import Any

import httpcore
import httpx

SocketOption = (
    tuple[int, int, int]
    | tuple[int, int, bytes | bytearray]
    | tuple[int, int, None, int]
)


class PinnedSocketStream(httpcore.NetworkStream):
    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        try:
            self._sock.settimeout(timeout)
            return self._sock.recv(max_bytes)
        except socket.timeout as exc:
            raise httpcore.ReadTimeout(str(exc)) from exc
        except OSError as exc:
            raise httpcore.ReadError(str(exc)) from exc

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        try:
            self._sock.settimeout(timeout)
            self._sock.sendall(buffer)
        except socket.timeout as exc:
            raise httpcore.WriteTimeout(str(exc)) from exc
        except OSError as exc:
            raise httpcore.WriteError(str(exc)) from exc

    def close(self) -> None:
        self._sock.close()

    def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore.NetworkStream:
        try:
            self._sock.settimeout(timeout)
            wrapped = ssl_context.wrap_socket(self._sock, server_hostname=server_hostname)
            return PinnedSocketStream(wrapped)
        except socket.timeout as exc:
            self.close()
            raise httpcore.ConnectTimeout(str(exc)) from exc
        except OSError as exc:
            self.close()
            raise httpcore.ConnectError(str(exc)) from exc

    def get_extra_info(self, info: str) -> Any:
        if info == "ssl_object" and isinstance(self._sock, ssl.SSLSocket):
            return self._sock
        if info == "client_addr":
            return self._sock.getsockname()
        if info == "server_addr":
            return self._sock.getpeername()
        if info == "socket":
            return self._sock
        return None


class PinnedNetworkBackend(httpcore.NetworkBackend):
    """Connect an already-validated hostname only to pre-resolved IPs.

    The original hostname remains inside httpcore's origin, so TLS SNI and certificate
    validation continue to use the hostname while TCP is pinned to a validated IP.
    """

    def __init__(self, hostname: str, validated_ips: list[str]) -> None:
        if not validated_ips:
            raise ValueError("validated_ips must not be empty")
        self.hostname = hostname.rstrip(".").lower()
        self.validated_ips = tuple(validated_ips)

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[SocketOption] | None = None,
    ) -> httpcore.NetworkStream:
        normalized = host.rstrip(".").lower()
        if normalized != self.hostname:
            raise httpcore.ConnectError(
                f"pinned transport refused unexpected hostname {host!r}; expected {self.hostname!r}"
            )
        last_error: Exception | None = None
        source_address = None if local_address is None else (local_address, 0)
        for ip in self.validated_ips:
            try:
                sock = socket.create_connection((ip, port), timeout, source_address=source_address)
                for option in socket_options or ():
                    sock.setsockopt(*option)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                return PinnedSocketStream(sock)
            except socket.timeout as exc:
                last_error = httpcore.ConnectTimeout(str(exc))
            except OSError as exc:
                last_error = httpcore.ConnectError(str(exc))
        if last_error is not None:
            raise last_error
        raise httpcore.ConnectError("no validated destination IP was connectable")

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[SocketOption] | None = None,
    ) -> httpcore.NetworkStream:
        raise httpcore.ConnectError("UNIX sockets are not supported by pinned HTTP replay")


class PinnedHTTPTransport(httpx.HTTPTransport):
    def __init__(
        self,
        hostname: str,
        validated_ips: list[str],
        *,
        http2: bool = True,
    ) -> None:
        super().__init__(verify=True, trust_env=False, http1=True, http2=http2, retries=0)
        self._pool.close()
        self._pool = httpcore.ConnectionPool(
            ssl_context=httpx.create_ssl_context(verify=True, trust_env=False),
            max_connections=1,
            max_keepalive_connections=0,
            http1=True,
            http2=http2,
            retries=0,
            network_backend=PinnedNetworkBackend(hostname, validated_ips),
        )
