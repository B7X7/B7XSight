import re
from urllib.parse import urlsplit

from utils.http import HTTP_ERRORS, error_message, request
from utils.url import normalize_url


COOKIE_NAME = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")


def cookie_attributes(field):
    pair, _, attributes = field.partition(";")
    name, separator, _ = pair.partition("=")
    name = name.strip()
    if not separator or not COOKIE_NAME.fullmatch(name):
        return None, {}
    flags = {}
    for attribute in attributes.split(";"):
        key, _, value = attribute.partition("=")
        flags[key.strip().lower()] = value.strip()
    return name, flags


def check_cookie_security(target):
    target = normalize_url(target)
    try:
        with request(target) as response:
            print(f"Cookie security (HTTP {response.status})")
            fields = response.headers.get_all("Set-Cookie", [])
            if not fields:
                print("No Set-Cookie fields on this response.")
            for number, field in enumerate(fields, 1):
                name, flags = cookie_attributes(field)
                if name is None:
                    print(f"Cookie #{number}: malformed Set-Cookie field")
                    continue

                secure = "Secure" if "secure" in flags else "Secure missing"
                http_only = "HttpOnly" if "httponly" in flags else "HttpOnly missing"
                same_site = flags.get("samesite", "").lower()
                if same_site == "none" and "secure" not in flags:
                    policy = "SameSite=None requires Secure"
                elif same_site in ("strict", "lax", "none"):
                    policy = f"SameSite={same_site.title()}"
                else:
                    policy = "SameSite missing or unrecognized"
                print(f"Cookie #{number} ({name}): {secure}, {http_only}, {policy}")
                for issue in cookie_issues(name, flags, urlsplit(target).scheme):
                    print(f"  {issue}")
    except HTTP_ERRORS as error:
        print(f"Cookie check failed: {error_message(error)}.")
        return False
    return True


def cookie_issues(name, flags, scheme):
    issues = []
    if name.startswith(("__Secure-", "__Host-", "__Http-")):
        if "secure" not in flags or scheme != "https":
            issues.append("Cookie prefix requires Secure and HTTPS.")
    if name.startswith("__Host-"):
        if flags.get("path") != "/" or "domain" in flags:
            issues.append("Host-prefixed cookies require Path=/ and no Domain attribute.")
    if name.startswith(("__Http-", "__Host-Http-")) and "httponly" not in flags:
        issues.append("HTTP-prefixed cookies require HttpOnly.")
    if "partitioned" in flags and "secure" not in flags:
        issues.append("Partitioned cookies require Secure.")
    return issues
