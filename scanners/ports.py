import socket
from urllib.parse import urlsplit

from utils.http import error_message
from utils.url import normalize_url


def check_ports(target):
    url = urlsplit(normalize_url(target))
    ports = (url.port,) if url.port is not None else (80, 443)
    completed = True
    for port in ports:
        try:
            with socket.create_connection((url.hostname, port), timeout=2):
                result = "open"
        except ConnectionRefusedError:
            result = "connection refused"
        except TimeoutError:
            result = "timed out"
            completed = False
        except OSError as error:
            result = error_message(error)
            completed = False
        print(f"TCP {port}: {result}")
    return completed
