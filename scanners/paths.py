from utils.http import HTTP_ERRORS, error_message, request


def check_sensitive_path(target):
    try:
        with request(target, method="HEAD") as response:
            status = response.status
            if 200 <= status < 300:
                result = "server returned success for HEAD"
            elif status in (401, 403):
                result = "access restricted"
            elif status in (404, 410):
                result = "server reported the path missing"
            elif status in (405, 501):
                result = "server did not accept HEAD"
            elif status in (301, 302, 303, 307, 308):
                result = "redirect"
            else:
                result = "result inconclusive"
            print(f"Path check (HTTP {status}): {result}.")
    except HTTP_ERRORS as error:
        print(f"Path check failed: {error_message(error)}.")
        return False
    return True
