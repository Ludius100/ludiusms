import json
import urllib.request

from config import JELLYFIN, KEY_FILE


def jellyfin_get(path):
    """Fetch and decode a JSON response from the configured Jellyfin API."""
    with open(KEY_FILE, "r") as f:
        key = f.read().strip()

    req = urllib.request.Request(
        JELLYFIN + path,
        headers={
            "Authorization": f'MediaBrowser Token="{key}"'
        }
    )

    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read())


def get_jellyfin_library_items():
    """Fetch movie and episode metadata used by the activity collector."""
    path = (
        "/Items"
        "?Recursive=true"
        "&IncludeItemTypes=Movie,Episode"
        "&Fields=DateCreated,Path,SeriesName,"
        "ParentIndexNumber,IndexNumber,ProductionYear"
    )

    data = jellyfin_get(path)

    if not isinstance(data, dict):
        return []

    return data.get("Items", [])
