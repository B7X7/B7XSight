import requests

SECURITY_HEADERS = {
    "Strict-Transport-Security": "HIGH",
    "Content-Security-Policy": "HIGH",
    "X-Content-Type-Options": "MEDIUM",
    "X-Frame-Options": "MEDIUM",
    "X-XSS-Protection": "LOW",
    "Referrer-Policy": "LOW",
    "Permissions-Policy": "LOW",
}


def check_security_headers(target):
    try:
        response = requests.get(target, timeout=10)
        print(f"\nTarget     : {target}")
        print(f"Status Code: {response.status_code}")
        print("-" * 40)

        for header, risk in SECURITY_HEADERS.items():
            if header in response.headers:
                print(f"[Found]   {header}")
            else:
                print(f"[Missing] {header} - Risk: {risk}")

        print("-" * 40)

    except requests.exceptions.RequestException as error:
        print(f"Scan failed for {target}: {error}")
