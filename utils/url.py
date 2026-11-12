"""Validate and normalize targets before they reach the scanners."""

import ipaddress
import re
from urllib.parse import quote, urlsplit, urlunsplit


DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
PORT = re.compile(r":[0-9]{1,5}", re.ASCII)


def normalize_url(target):
    if not target or "\\" in target or any(
        char.isspace() or not char.isprintable() for char in target
    ):
        raise ValueError("Enter an HTTP(S) URL or hostname without spaces or controls.")

    if not SCHEME.match(target):
        target = "https://" + target

    try:
        url = urlsplit(target)
        host = url.hostname
        port = url.port
        if url.scheme not in ("http", "https") or not host or "@" in url.netloc:
            raise ValueError

        bracketed = url.netloc.startswith("[")
        if bracketed:
            suffix = url.netloc.partition("]")[2]
        else:
            _, separator, port_text = url.netloc.partition(":")
            suffix = separator + port_text

        if suffix and (not PORT.fullmatch(suffix) or not port):
            raise ValueError

        if bracketed:
            if "%" in host:
                raise ValueError
            host = f"[{ipaddress.IPv6Address(host)}]"
        else:
            host = host.encode("idna").decode("ascii").lower()
            labels = host.removesuffix(".").split(".")
            if len(host.removesuffix(".")) > 253 or not all(
                DNS_LABEL.fullmatch(label) for label in labels
            ):
                raise ValueError

        authority = f"{host}:{port}" if port is not None else host
        path = quote(url.path or "/", safe="/%:@!$&'()*+,;=-._~")
        query = quote(url.query, safe="/?%:@!$&'()*+,;=-._~[]")
    except ValueError:
        raise ValueError("Enter a valid HTTP(S) target without credentials.") from None

    return urlunsplit((url.scheme, authority, path, query, ""))


def is_valid_url(url):
    try:
        normalize_url(url)
    except ValueError:
        return False
    return True


def display_url(target):
    url = urlsplit(target)
    return urlunsplit((url.scheme, url.netloc, url.path, "", "")) + (
        "?[redacted]" if url.query else ""
    )
