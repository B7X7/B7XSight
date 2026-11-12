from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from urllib.parse import urlsplit

from utils.http import HTTP_ERRORS, error_message, read_document, request
from utils.url import is_valid_url


DOCUMENTS = {"/robots.txt": 512_000, "/sitemap.xml": 1_048_576}
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def analyze_robots(body):
    text = body.decode("utf-8-sig")
    counts = dict.fromkeys(("user-agent", "allow", "disallow", "sitemap"), 0)
    for line in text.splitlines():
        key, separator, _ = line.partition("#")[0].partition(":")
        key = key.strip().lower()
        if separator and key in counts:
            counts[key] += 1
    if not any(counts.values()):
        print("  No recognized directives.")
        return
    for key, count in counts.items():
        print(f"  {key} directives: {count}")


def analyze_sitemap(body):
    root = ElementTree.fromstring(body, forbid_dtd=True)
    entries = {
        SITEMAP_NS + "urlset": ("url", "URL entries"),
        SITEMAP_NS + "sitemapindex": ("sitemap", "sitemap references"),
    }
    if root.tag not in entries:
        print("  Unrecognized sitemap root or namespace.")
        return False
    tag, label = entries[root.tag]
    items = root.findall(SITEMAP_NS + tag)
    locations = [
        (item.findtext(SITEMAP_NS + "loc") or "").strip() for item in items
    ]
    with_location = sum(bool(location) for location in locations)
    print(f"  {label}: {len(items)} ({len(items) - with_location} without a location).")
    valid_locations = []
    invalid = 0
    for location in filter(None, locations):
        if not is_valid_url(location) or urlsplit(location).scheme not in ("http", "https"):
            invalid += 1
        else:
            valid_locations.append(location)
    print(f"  Invalid locations: {invalid}")
    print(f"  Duplicate locations: {len(valid_locations) - len(set(valid_locations))}")
    return True


def check_robots_and_sitemap(target):
    completed = True
    for path, analyze in (("/robots.txt", analyze_robots), ("/sitemap.xml", analyze_sitemap)):
        try:
            with request(target, path=path) as response:
                print(f"{path} (HTTP {response.status})")
                if response.status != 200:
                    print("  Analysis requires HTTP 200.")
                    completed = False
                    continue
                body = read_document(response, DOCUMENTS[path])
            if analyze(body) is False:
                completed = False
        except HTTP_ERRORS as error:
            print(f"{path}: {error_message(error)}.")
            completed = False
        except (UnicodeError, ElementTree.ParseError, DefusedXmlException, LookupError):
            print(f"{path}: malformed or unsupported document.")
            completed = False
        except ValueError as error:
            print(f"{path}: {error}.")
            completed = False
    return completed
