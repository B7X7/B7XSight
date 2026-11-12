from time import perf_counter

from utils.http import HTTP_ERRORS, error_message, request


def check_connection(target):
    started = perf_counter()
    try:
        with request(target) as response:
            print(f"HTTP response received (status {response.status}).")
            print(f"Response headers received in {(perf_counter() - started) * 1000:.0f} ms.")
    except HTTP_ERRORS as error:
        print(f"Connection failed ({type(error).__name__}): {error_message(error)}.")
        return False
    return True
