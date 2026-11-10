"""Bounded HTTP GET transport with DNS pinning and redirects disabled.

Only globally routable destination IPs are accepted. DNS is resolved once per
request and the socket connects to that validated address, while TLS still
verifies the original hostname. Redirect responses are returned, never followed.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from urllib.parse import SplitResult
from urllib.parse import urlsplit


def validate_url(url: str) -> tuple[SplitResult, str, int, str, str]:
    """Validate an absolute HTTP(S) URL and resolve a globally routable address."""
    if not isinstance(url, str) or any(char.isspace() for char in url):
        raise ValueError("URL must be a whitespace-free absolute HTTP(S) URL")
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        raise ValueError("URL must be an absolute http:// or https:// URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing embedded credentials are not allowed")
    if parsed.fragment:
        raise ValueError("URL fragments are not allowed")
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError as exc:
        raise ValueError("URL contains an invalid port") from exc
    if not 1 <= port <= 65535:
        raise ValueError("URL port is out of range")

    host = parsed.hostname
    try:
        literal = ipaddress.ip_address(host)
        addresses = [str(literal)]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise OSError(f"DNS resolution failed: {exc}") from exc
        addresses = list(dict.fromkeys(record[4][0] for record in records))
    if not addresses:
        raise OSError("DNS returned no usable addresses")
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
        if not ip.is_global:
            raise ValueError("Destination resolves to a non-public IP address")
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return parsed, host, port, addresses[0], path


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, address: str, timeout: float):
        super().__init__(host, port, timeout=timeout)
        self._pinned_address = address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )


class _PinnedHTTPSConnection(_PinnedHTTPConnection):
    def connect(self) -> None:
        raw = socket.create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )
        try:
            self.sock = ssl.create_default_context().wrap_socket(
                raw, server_hostname=self.host
            )
        except Exception:
            raw.close()
            raise


def safe_get(url: str, *, timeout: float = 10.0, max_bytes: int = 1_000_000,
             user_agent: str = "Software-QA-Lab/1.0") -> tuple[int, dict[str, str], bytes]:
    """Perform one GET without proxy use or redirect following."""
    if not 0 < timeout <= 60:
        raise ValueError("timeout must be greater than 0 and at most 60 seconds")
    if not 1 <= max_bytes <= 5_000_000:
        raise ValueError("max_bytes must be between 1 and 5,000,000")
    parsed, host, port, address, path = validate_url(url)
    is_https = parsed.scheme.lower() == "https"
    connection_type = _PinnedHTTPSConnection if is_https else _PinnedHTTPConnection
    connection = connection_type(host, port, address, timeout)
    host_header = host
    if (is_https and port != 443) or (not is_https and port != 80):
        host_header = f"{host}:{port}"
    try:
        connection.request("GET", path, headers={
            "Host": host_header,
            "User-Agent": user_agent,
            "Connection": "close",
        })
        response = connection.getresponse()
        body = response.read(max_bytes + 1)
        return response.status, dict(response.getheaders()), body
    finally:
        connection.close()
