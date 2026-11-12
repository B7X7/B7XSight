"""Perform one request on the selected origin with verified TLS."""

from contextlib import contextmanager
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from time import monotonic
import socket
import ssl
from urllib.parse import urlsplit

from utils.url import normalize_url


TIMEOUT = 5
HTTP_ERRORS = (OSError, HTTPException)


def error_message(error):
    if isinstance(error, ssl.SSLCertVerificationError):
        return "TLS certificate verification failed"
    if isinstance(error, ssl.SSLError):
        return "TLS handshake failed"
    if isinstance(error, socket.gaierror):
        return "hostname could not be resolved"
    if isinstance(error, TimeoutError):
        return "connection or response timed out"
    if isinstance(error, ConnectionRefusedError):
        return "server refused the connection"
    if isinstance(error, HTTPException):
        return "invalid or incomplete HTTP response"
    return "network connection failed"


@contextmanager
def request(target, *, method="GET", path=None):
    url = urlsplit(normalize_url(target))
    connection_type = HTTPSConnection if url.scheme == "https" else HTTPConnection
    port = url.port or connection_type.default_port
    connection = connection_type(url.hostname, port, timeout=TIMEOUT)
    resource = url.path + ("?" + url.query if url.query else "")
    try:
        connection.request(
            method,
            resource if path is None else path,
            headers={
                "User-Agent": "B7XSight",
                "Connection": "close",
                "Accept-Encoding": "identity",
            },
        )
        with connection.getresponse() as response:
            yield response
    finally:
        connection.close()


def read_document(response, limit):
    if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
        raise ValueError("unsupported content encoding")
    deadline = monotonic() + TIMEOUT
    body = bytearray()
    while len(body) <= limit:
        if monotonic() >= deadline:
            raise TimeoutError
        chunk = response.read1(min(8192, limit + 1 - len(body)))
        if not chunk:
            if response.length:
                raise ValueError("incomplete response body")
            return bytes(body)
        body.extend(chunk)
    raise ValueError("response exceeds the analysis size limit")
