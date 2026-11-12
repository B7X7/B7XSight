from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from utils.http import HTTP_ERRORS, read_document, request


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
        return
    tag, label = entries[root.tag]
    items = root.findall(SITEMAP_NS + tag)
    with_location = sum(
        bool((item.findtext(SITEMAP_NS + "loc") or "").strip()) for item in items
    )
    print(f"  {label}: {len(items)} ({len(items) - with_location} without a location).")


def check_robots_and_sitemap(target):
    for path, analyze in (("/robots.txt", analyze_robots), ("/sitemap.xml", analyze_sitemap)):
        try:
            with request(target, path=path) as response:
                print(f"{path} (HTTP {response.status})")
                if response.status != 200:
                    print("  Analysis requires HTTP 200.")
                    continue
                body = read_document(response, DOCUMENTS[path])
            analyze(body)
        except HTTP_ERRORS as error:
            print(f"{path}: request failed ({type(error).__name__}).")
        except (UnicodeError, ElementTree.ParseError, DefusedXmlException, LookupError):
            print(f"{path}: malformed or unsupported document.")
        except ValueError as error:
            print(f"{path}: {error}.")
