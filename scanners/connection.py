import requests


def check_connection(target):
    try:
        response = requests.get(target, timeout=10)
        print("Connection successful")
        print("Status code:", response.status_code)

    except requests.RequestException as error:
        print("Connection failed")
        print("Error:", error)