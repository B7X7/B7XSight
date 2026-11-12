from urllib.parse import urlsplit

from utils.http import HTTP_ERRORS, request


def check_sensitive_path(target):
    if urlsplit(target).path in ("", "/"):
        print("Set the target to the exact authorized path you want to check.")
        return

    try:
        with request(target, method="HEAD") as response:
            status = response.status
            if 200 <= status < 300:
                result = "reachable by HEAD; verify whether this is the expected resource"
            elif status in (401, 403):
                result = "access restricted for this request"
            elif status in (404, 410):
                result = "path reported absent"
            elif 300 <= status < 400:
                result = "redirect; result inconclusive"
            else:
                result = "result inconclusive"
            print(f"Path check (HTTP {status}): {result}.")
    except HTTP_ERRORS as error:
        print(f"Path check failed ({type(error).__name__}).")
