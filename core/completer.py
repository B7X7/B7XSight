import readline


MAIN_COMMANDS = [
    "set",
    "show",
    "run",
    "clear",
    "help",
    "exit"
]


SET_OPTIONS = [
    "target",
    "mode"
]


SHOW_OPTIONS = [
    "target",
    "mode"
]


MODE_OPTIONS = [
    "connection",
    "headers",
    "cookies",
    "paths",
    "ports"
]


def completer(text, state):
    line = readline.get_line_buffer()
    parts = line.split()

    matches = []

    # First command completion
    # Example: r<Tab> -> run
    if len(parts) == 0:
        matches = MAIN_COMMANDS

    elif len(parts) == 1 and not line.endswith(" "):
        matches = [
            command for command in MAIN_COMMANDS
            if command.startswith(text.lower())
        ]

    # After first command
    # Example: set <Tab> -> target, mode
    elif len(parts) == 1 and line.endswith(" "):
        first = parts[0].lower()

        if first == "set":
            matches = SET_OPTIONS

        elif first == "show":
            matches = SHOW_OPTIONS

    # Completing second word
    # Example: set t<Tab> -> target
    elif len(parts) == 2 and not line.endswith(" "):
        first = parts[0].lower()

        if first == "set":
            matches = [
                option for option in SET_OPTIONS
                if option.startswith(text.lower())
            ]

        elif first == "show":
            matches = [
                option for option in SHOW_OPTIONS
                if option.startswith(text.lower())
            ]

    # After "set mode "
    # Example: set mode <Tab> -> connection, headers, cookies, paths, ports
    elif len(parts) == 2 and line.endswith(" "):
        first = parts[0].lower()
        second = parts[1].lower()

        if first == "set" and second == "mode":
            matches = MODE_OPTIONS

    # Completing mode value
    # Example: set mode h<Tab> -> headers
    elif len(parts) == 3:
        first = parts[0].lower()
        second = parts[1].lower()

        if first == "set" and second == "mode":
            matches = [
                mode for mode in MODE_OPTIONS
                if mode.startswith(text.lower())
            ]

    if state < len(matches):
        return matches[state] + " "

    return None