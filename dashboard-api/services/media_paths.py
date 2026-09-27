import os


def safe_media_component(value, fallback="media"):
    """Return one safe filesystem path component while keeping Unicode names."""
    value = str(value or "").strip()
    cleaned = []

    for char in value:
        if char in '/\\' or ord(char) < 32:
            cleaned.append("_")
        elif char in '<>:"|?*':
            cleaned.append("_")
        else:
            cleaned.append(char)

    value = "".join(cleaned).strip(" .")

    if value in ("", ".", ".."):
        value = fallback

    return value[:180]


def path_is_inside(child, parent):
    child = os.path.realpath(child)
    parent = os.path.realpath(parent)

    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        return False
