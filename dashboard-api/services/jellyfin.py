import json
import urllib.request

from config import JELLYFIN, KEY_FILE


def jellyfin_request(path):
    """Build an authenticated Jellyfin request."""
    with open(KEY_FILE, "r") as f:
        key = f.read().strip()

    return urllib.request.Request(
        JELLYFIN + path,
        headers={
            "Authorization": f'MediaBrowser Token="{key}"'
        }
    )


def jellyfin_get(path):
    """Fetch and decode a JSON response from the configured Jellyfin API."""
    with urllib.request.urlopen(jellyfin_request(path), timeout=5) as response:
        return json.loads(response.read())


def jellyfin_raw(path):
    """Fetch binary data from Jellyfin."""
    with urllib.request.urlopen(jellyfin_request(path), timeout=8) as response:
        return response.read(), response.headers.get_content_type()


def get_jellyfin_summary():
    """Build the dashboard summary from Jellyfin counts and sessions."""
    counts = jellyfin_get("/Items/Counts")
    sessions = jellyfin_get("/Sessions")

    active_sessions = sum(
        1 for session in sessions
        if session.get("NowPlayingItem")
    )

    return {
        "online": True,
        "movies": counts.get("MovieCount", 0),
        "series": counts.get("SeriesCount", 0),
        "episodes": counts.get("EpisodeCount", 0),
        "songs": counts.get("SongCount", 0),
        "activeSessions": active_sessions,
    }


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


def get_jellyfin_recent(limit=8):
    """Return recent Movie/Series entries for the dashboard."""
    safe_limit = max(1, min(int(limit or 8), 12))
    path = (
        "/Items"
        "?Recursive=true"
        "&IncludeItemTypes=Movie,Series"
        "&SortBy=DateCreated"
        "&SortOrder=Descending"
        f"&Limit={safe_limit}"
        "&Fields=DateCreated,ProductionYear,ImageTags"
    )
    data = jellyfin_get(path)
    result = []

    for item in data.get("Items", []) if isinstance(data, dict) else []:
        item_id = item.get("Id")
        if not item_id:
            continue
        result.append({
            "id": item_id,
            "name": item.get("Name") or "Bez tytułu",
            "type": item.get("Type") or "",
            "year": item.get("ProductionYear"),
            "hasImage": bool((item.get("ImageTags") or {}).get("Primary")),
        })

    return {"items": result}
