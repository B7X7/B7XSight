def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                          B7XSight                            ║
║                                                              ║
║                     Web Security Scanner                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    print("Author : Bandr Alghamdi")
    print("Mode   : Terminal CLI")
    print("-" * 64)
    print("  USAGE:")
    print("    set target <url>       Set the target URL")
    print("    show target            Show current target")
    print("    run                    Start scanning")
    print("    help                   Show available commands")
    print("    exit                   Quit the tool")
    print("-" * 64)
    print("  EXAMPLE:")
    print("    set target example.com")
    print("    run")
    print("-" * 64)


def print_help():
    print("""
Available commands:
  set target <url>       Set the target URL
  set mode <mode>        Set scan mode
  show target            Show current target
  show mode              Show current scan mode
  run                    Start scanning
  clear                  Clear the terminal screen
  help                   Show available commands
  exit                   Quit the tool

Available modes:
  connection             Check if target is reachable
  headers                Scan security headers
  cookies                Scan cookie security flags
  paths                  Search common sensitive paths
  ports                  Scan basic ports
""")