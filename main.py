import requests


def normalize_url(target):
    if target.startswith("http://") or target.startswith("https://"):
        return target
    else:
        return "https://" + target


def check_connection(target):
    try:
        response = requests.get(target, timeout=10)
        print("Connection successful")
        print("Status code:", response.status_code)
    except requests.RequestException:
        print("Connection failed")


def main():
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

    while True:
        target = input("Enter the target URL: ").strip()
        print("Target website: " + target)

        while True:
            choose = input("Is this the correct target? (Y OR N): ").lower().strip()

            if choose == "y":
                target = normalize_url(target)
                print("Start scanning: " + target)
                check_connection(target)
                return

            elif choose == "n":
                print("Please enter the URL again")
                print("-" * 64)
                break

            else:
                print("Invalid choice. Please choose Y or N.")


main()