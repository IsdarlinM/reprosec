from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

MAX_IMPORT_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000
MAX_TOTAL_UNCOMPRESSED = 200 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100


def validate_external_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only absolute http/https URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("credentials in URLs are not accepted")


def resolve_ips(url: str) -> list[str]:
    validate_external_url(url)
    host = urlsplit(url).hostname
    assert host
    ips = {str(row[4][0]) for row in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
    return sorted(ips)


def is_private_or_special(ip: str) -> bool:
    obj = ipaddress.ip_address(ip)
    return obj.is_private or obj.is_loopback or obj.is_link_local or obj.is_reserved
