import json
import os

from config import JELLYFIN_STATE_FILE


def load_jellyfin_state():
    """Load the persisted Jellyfin activity collector state."""
    try:
        with open(JELLYFIN_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except FileNotFoundError:
        pass

    except Exception as e:
        print(
            "Jellyfin state load error:",
            type(e).__name__,
            e,
            flush=True
        )

    return {}


def save_jellyfin_state(state):
    """Persist Jellyfin activity collector state atomically."""
    directory = os.path.dirname(JELLYFIN_STATE_FILE)
    os.makedirs(directory, exist_ok=True)
    temporary = JELLYFIN_STATE_FILE + ".tmp"

    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    os.replace(temporary, JELLYFIN_STATE_FILE)


def build_jellyfin_activity_state(items):
    """Build collector state from Jellyfin movie and episode metadata."""
    current = {}

    for item in items:
        item_id = str(item.get("Id") or "").strip()
        if not item_id:
            continue

        current[item_id] = {
            "type": item.get("Type"),
            "name": item.get("Name"),
            "seriesName": item.get("SeriesName"),
            "season": item.get("ParentIndexNumber"),
            "episode": item.get("IndexNumber"),
            "year": item.get("ProductionYear"),
            "dateCreated": item.get("DateCreated"),
            "path": item.get("Path")
        }

    return current


def format_episode_detail(item):
    season = item.get("season")
    episode = item.get("episode")
    episode_name = str(item.get("name") or "").strip()

    if season is not None and episode is not None:
        code = f"S{int(season):02d}E{int(episode):02d}"
    elif episode is not None:
        code = f"E{int(episode):02d}"
    else:
        code = ""

    generic_names = set()
    if episode is not None:
        generic_names.update({
            f"episode {episode}".lower(),
            f"odcinek {episode}".lower()
        })

    if episode_name.lower() in generic_names:
        episode_name = ""

    if code and episode_name:
        return f"{code} • {episode_name}"
    if code:
        return code
    if episode_name:
        return episode_name
    return None
