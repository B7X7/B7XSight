import os
import sys
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
from pathlib import Path

from core.banner import print_banner, print_help
from core.completer import configure_completion
from core.report import save_report
from scanners.connection import check_connection
from scanners.cookies import check_cookie_security
from scanners.headers import check_security_headers
from scanners.paths import check_sensitive_path
from scanners.ports import check_ports
from scanners.robots import check_robots_and_sitemap
from utils.url import display_url, normalize_url


MODES = {
    "connection": (check_connection, "Show the HTTP status"),
    "headers": (check_security_headers, "Check security headers"),
    "cookies": (check_cookie_security, "Check cookie flags"),
    "paths": (check_sensitive_path, "Send a HEAD request to the target URL"),
    "robots": (check_robots_and_sitemap, "Summarize robots.txt and sitemap.xml"),
    "ports": (check_ports, "Check the target port or TCP ports 80 and 443"),
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
            print(f"Running {mode} on {display_url(target)}")
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


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="B7XSight web server checks by Bandr Alghamdi.",
        epilog="Run without arguments to open the interactive console.",
    )
    parser.add_argument("--target", help="HTTP(S) URL or hostname")
    parser.add_argument("--mode", choices=MODES, help="check to run")
    parser.add_argument("--output", type=Path, help="write a JSON report")
    args = parser.parse_args(argv)
    if args.target is None and args.mode is None and args.output is None:
        main()
        return 0
    if args.target is None or args.mode is None:
        parser.error("--target and --mode are required together")
    try:
        target = normalize_url(args.target)
    except ValueError as error:
        parser.error(str(error))
    if args.output is not None:
        if not args.output.parent.is_dir() or args.output.is_dir():
            parser.error("--output must name a file in an existing directory")

    print(f"Running {args.mode} on {display_url(target)}")
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            completed = MODES[args.mode][0](target)
    except KeyboardInterrupt:
        print(output.getvalue(), end="")
        print("Check cancelled.", file=sys.stderr)
        return 130
    print(output.getvalue(), end="")
    if args.output is not None:
        report = {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target": display_url(target),
            "mode": args.mode,
            "completed": completed,
            "output": output.getvalue().splitlines(),
        }
        try:
            save_report(args.output, report)
        except OSError:
            print("Could not save the report. Check the output path and write access.", file=sys.stderr)
            return 1
        print(f"Report saved to {ascii(str(args.output))}")
    return 0 if completed else 1


if __name__ == "__main__":
    sys.exit(cli())
