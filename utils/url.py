def normalize_url(target):
    if target.startswith("http://") or target.startswith("https://"):
        return target
    else:
        return "https://" + target


def is_valid_url(url):
    if url == "":
        return False
    if " " in url:
        return False
    if "." not in url:
        return False
    return True