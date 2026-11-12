from utils.http import HTTP_ERRORS, request


def check_connection(target):
    try:
        with request(target) as response:
            print(f"HTTP response received (status {response.status}).")
    except HTTP_ERRORS as error:
        print(f"Connection failed ({type(error).__name__}).")
