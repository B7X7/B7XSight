import readline

from core.banner import print_banner, print_help
from core.completer import completer
from utils.url import normalize_url, is_valid_url
from scanners.connection import check_connection



VALID_MODES = [
    "connection",
    "headers",
    "cookies",
    "paths",
    "ports"
]


def main():
    target = None
    mode = None

    # Enable tab auto-completion
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set show-all-if-ambiguous on")

    print_banner()

    while True:
        command = input("B7XSight> ").strip()

        if command == "":
            continue

        command_lower = command.lower()
        parts = command.split(maxsplit=2)

        # -----------------------------
        # SET command
        # -----------------------------
        if parts[0].lower() == "set":

            if len(parts) == 1:
                print("Set what?")
                print("Usage:")
                print("  set target <url>")
                print("  set mode <mode>")

            elif parts[1].lower() == "target":

                if len(parts) < 3:
                    print("Please provide a target URL")
                    print("Example: set target example.com")

                else:
                    target_value = parts[2].strip()

                    if not is_valid_url(target_value):
                        print("Invalid target")
                        print("Target must not be empty or contain spaces")
                        print("Example: set target example.com")

                    else:
                        target = normalize_url(target_value)
                        print("Target website:", target)

            elif parts[1].lower() == "mode":

                if len(parts) < 3:
                    print("Please provide a scan mode")
                    print("Available modes: connection, headers, cookies, paths, ports")
                    print("Example: set mode headers")

                else:
                    mode_value = parts[2].strip().lower()

                    if mode_value not in VALID_MODES:
                        print("Invalid scan mode")
                        print("Available modes: connection, headers, cookies, paths, ports")

                    else:
                        mode = mode_value
                        print("Scan mode:", mode)

            else:
                print("Invalid set option")
                print("Available set options: target, mode")
                print("Usage:")
                print("  set target <url>")
                print("  set mode <mode>")

        # -----------------------------
        # SHOW command
        # -----------------------------
        elif parts[0].lower() == "show":

            if len(parts) == 1:
                print("Show what?")
                print("Usage:")
                print("  show target")
                print("  show mode")

            elif parts[1].lower() == "target":
                if target:
                    print("Current target:", target)
                else:
                    print("No target set yet")

            elif parts[1].lower() == "mode":
                if mode:
                    print("Current scan mode:", mode)
                else:
                    print("No scan mode set yet")

            else:
                print("Invalid show option")
                print("Available show options: target, mode")

        # -----------------------------
        # RUN command
        # -----------------------------
        elif command_lower == "run":

            if not target:
                print("Please set the target URL first using 'set target <url>'")

            elif not mode:
                print("Please set the scan mode first using 'set mode <mode>'")
                print("Available modes: connection, headers, cookies, paths, ports")

            else:
                print("Start scanning:", target)
                print("Running mode:", mode)

                if mode == "connection":
                    check_connection(target)

                elif mode == "headers":
                    print("Headers scanner is not added yet")

                elif mode == "cookies":
                    print("Cookies scanner is not added yet")

                elif mode == "paths":
                    print("Paths scanner is not added yet")

                elif mode == "ports":
                    print("Basic port scanner is not added yet")

        # -----------------------------
        # HELP command
        # -----------------------------
        elif command_lower == "help":
            print_help()

        # -----------------------------
        # CLEAR command
        # -----------------------------
        elif command_lower == "clear":
            print("\033c", end="")

        # -----------------------------
        # EXIT command
        # -----------------------------
        elif command_lower == "exit":
            print("Exiting B7XSight. Goodbye!")
            break

        # -----------------------------
        # INVALID command
        # -----------------------------
        else:
            print("*Invalid command*")
            print("Type 'help' to see available commands")

if __name__ == "__main__":
    main()