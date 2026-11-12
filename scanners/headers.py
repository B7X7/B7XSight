import re
from urllib.parse import urlsplit

from utils.http import HTTP_ERRORS, error_message, request
from utils.url import normalize_url


SECURITY_HEADERS = (
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
)
REFERRER_POLICIES = {
    "no-referrer", "no-referrer-when-downgrade", "origin",
    "origin-when-cross-origin", "same-origin", "strict-origin",
    "strict-origin-when-cross-origin", "unsafe-url",
}
MAX_AGE = re.compile(r'max-age\s*=\s*(?:"([0-9]+)"|([0-9]+))', re.IGNORECASE)


def header_status(header, values, scheme):
    if header == "Strict-Transport-Security" and scheme != "https":
        return "applies to HTTPS only"
    if not any(value.strip() for value in values):
        return "missing or empty"
    first = values[0].strip()
    if header == "Strict-Transport-Security":
        directives = [directive.strip() for directive in first.split(";")]
        max_ages = [
            directive for directive in directives
            if directive.partition("=")[0].strip().lower() == "max-age"
        ]
        age = MAX_AGE.fullmatch(max_ages[0]) if len(max_ages) == 1 else None
        if age is None:
            return "invalid or missing max-age"
        if not (age[1] or age[2]).lstrip("0"):
            return "disabled by max-age=0"
    elif header == "X-Content-Type-Options":
        if first.partition(",")[0].strip().lower() != "nosniff":
            return "expected nosniff"
    elif header == "X-Frame-Options":
        if not all(value.strip().upper() in ("DENY", "SAMEORIGIN") for value in values):
            return "unrecognized value"
        if len({value.strip().upper() for value in values}) > 1:
            return "conflicting values"
    elif header == "Referrer-Policy":
        policies = [
            token.strip() for value in values for token in value.split(",")
            if token.strip() in REFERRER_POLICIES
        ]
        if not policies:
            return "unrecognized policy"
        if policies[-1] == "unsafe-url":
            return "unsafe-url sends full referrers across origins"
    return "present"


def check_security_headers(target):
    target = normalize_url(target)
    try:
        with request(target) as response:
            print(f"Security headers (HTTP {response.status})")
            for header in SECURITY_HEADERS:
                values = response.headers.get_all(header, [])
                print(f"{header}: {header_status(header, values, urlsplit(target).scheme)}")
            if response.headers.get("X-XSS-Protection") is not None:
                print("X-XSS-Protection: legacy header")
            if response.headers.get("Content-Security-Policy-Report-Only"):
                print("Content-Security-Policy-Report-Only: monitoring policy")
            print("Header presence alone does not confirm effective protection.")
    except HTTP_ERRORS as error:
        print(f"Header check failed: {error_message(error)}.")
        return False
    return True
