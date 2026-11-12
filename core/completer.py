MAIN_COMMANDS = ("set", "show", "run", "clear", "help", "exit")
OPTIONS = ("target", "mode")


def suggestions(line, prefix, modes):
    preceding = line.split() if not prefix else line[: -len(prefix)].split()
    preceding = [word.lower() for word in preceding]
    if not preceding:
        choices = MAIN_COMMANDS
    elif preceding in (["set"], ["show"]):
        choices = OPTIONS
    elif preceding == ["set", "mode"]:
        choices = modes
    else:
        return []
    return [choice + " " for choice in choices if choice.startswith(prefix.lower())]


def configure_completion(modes):
    try:
        import readline
    except ImportError:
        return

    def complete(text, state):
        line = readline.get_line_buffer()[:readline.get_endidx()]
        matches = suggestions(line, text, modes)
        return matches[state] if state < len(matches) else None

    readline.set_completer(complete)
    if getattr(readline, "backend", "") == "editline" or "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
