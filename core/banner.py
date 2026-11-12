def print_banner():
    print("B7XSight | Web Security Scanner")
    print("Author: Bandr Alghamdi")
    print("Use only on systems you are authorized to assess.")
    print("Type 'help' for commands and scan modes.")


def print_help(modes):
    print("""
Available commands:
  set target <url>       Set the target URL
  set mode <mode>        Set scan mode
  show target            Show current target
  show mode              Show current scan mode
  run                    Run the selected check
  clear                  Clear the terminal screen
  help                   Show available commands
  exit                   Quit the tool

Available modes:""")
    for mode, (_, description) in modes.items():
        print(f"  {mode:22} {description}")
