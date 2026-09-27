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
