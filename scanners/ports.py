import socket
from urllib.parse import urlsplit


def check_ports(target):
    url = urlsplit(target)
    ports = (url.port,) if url.port is not None else (80, 443)
    for port in ports:
        try:
            with socket.create_connection((url.hostname, port), timeout=2):
                result = "open"
        except ConnectionRefusedError:
            result = "connection refused"
        except TimeoutError:
            result = "timed out"
        except OSError as error:
            result = f"connection failed ({type(error).__name__})"
        print(f"TCP {port}: {result}")
