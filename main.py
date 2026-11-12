import os
import sys

from core.banner import print_banner, print_help
from core.completer import configure_completion
from scanners.connection import check_connection
from scanners.cookies import check_cookie_security
from scanners.headers import check_security_headers
from scanners.paths import check_sensitive_path
from scanners.ports import check_ports
from scanners.robots import check_robots_and_sitemap
from utils.url import display_url, normalize_url


MODES = {
    "connection": (check_connection, "Check whether the target responds over HTTP"),
    "headers": (check_security_headers, "Inspect security response headers"),
    "cookies": (check_cookie_security, "Inspect Set-Cookie security attributes"),
    "paths": (check_sensitive_path, "Check the exact authorized path using HEAD"),
    "robots": (check_robots_and_sitemap, "Summarize robots.txt and sitemap.xml"),
    "ports": (check_ports, "Check the specified TCP port or ports 80 and 443"),
}


def main():
    target = None
    mode = None
    configure_completion(MODES)
    print_banner()

    while True:
        try:
            parts = input("B7XSight> ").strip().split(maxsplit=2)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not parts:
            continue

        command = parts[0].lower()
        option = parts[1].lower() if len(parts) > 1 else ""
        if command == "set":
            if len(parts) != 3 or option not in ("target", "mode"):
                print("Usage: set target <url> or set mode <mode>")
            elif option == "target":
                try:
                    target = normalize_url(parts[2])
                    print("Target:", display_url(target))
                except ValueError as error:
                    print(error)
            else:
                value = parts[2].lower()
                if value in MODES:
                    mode = value
                    print("Scan mode:", mode)
                else:
                    print("Available modes:", ", ".join(MODES))
        elif command == "show":
            if len(parts) != 2 or option not in ("target", "mode"):
                print("Usage: show target or show mode")
            elif option == "target":
                print("Current target:", display_url(target) if target else "(unset)")
            else:
                print("Current scan mode:", mode or "(unset)")
        elif len(parts) != 1:
            print("Invalid command. Type 'help' for usage.")
        elif command == "run":
            if not target or not mode:
                print("Set both target and mode before running a check.")
                continue
            try:
                MODES[mode][0](target)
            except KeyboardInterrupt:
                print("\nCheck cancelled.")
        elif command == "help":
            print_help(MODES)
        elif command == "clear":
            if sys.stdout.isatty():
                if os.name == "nt":
                    os.system("cls")
                else:
                    print("\033[2J\033[H", end="", flush=True)
        elif command == "exit":
            break
        else:
            print("Invalid command. Type 'help' for usage.")

    print("Exiting B7XSight.")


if __name__ == "__main__":
    main()
