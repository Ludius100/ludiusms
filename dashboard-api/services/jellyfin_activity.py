import json
import os
import threading
import time

from config import JELLYFIN_COLLECT_INTERVAL, JELLYFIN_STATE_FILE

from services.activity import add_activity
from services.jellyfin import get_jellyfin_library_items


_activity_collectors_lock = threading.Lock()
_activity_collectors_started = False


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


def collect_jellyfin_activity():
    try:
        items = get_jellyfin_library_items()
        current = build_jellyfin_activity_state(items)

        state_exists = os.path.exists(JELLYFIN_STATE_FILE)
        state = load_jellyfin_state()

        # Pierwszy przebieg tylko zapamiętuje aktualną bibliotekę.
        # Nie zasypujemy Activity starymi filmami i odcinkami.
        if not state_exists:
            save_jellyfin_state(current)
            print(
                f"Jellyfin activity baseline: {len(current)} items",
                flush=True
            )
            return

        old_ids = set(state.keys())
        new_ids = set(current.keys()) - old_ids
        new_items = [current[item_id] for item_id in new_ids]
        new_items.sort(key=lambda item: item.get("dateCreated") or "")

        for item in new_items:
            item_type = item.get("type")

            if item_type == "Movie":
                title = str(item.get("name") or "Nieznany film").strip()
                year = item.get("year")

                add_activity(
                    "movie_added",
                    title,
                    detail=str(year) if year else None,
                    source="jellyfin"
                )

                print(
                    "Activity: movie added: "
                    + title
                    + (f" ({year})" if year else ""),
                    flush=True
                )

            elif item_type == "Episode":
                title = str(
                    item.get("seriesName")
                    or item.get("name")
                    or "Nieznany serial"
                ).strip()
                detail = format_episode_detail(item)

                add_activity(
                    "episode_added",
                    title,
                    detail=detail,
                    source="jellyfin"
                )

                print(
                    "Activity: episode added: "
                    + title
                    + (f" • {detail}" if detail else ""),
                    flush=True
                )

        save_jellyfin_state(current)

    except Exception as e:
        print(
            "Jellyfin activity collector error:",
            type(e).__name__,
            e,
            flush=True
        )


def jellyfin_activity_loop():
    # Krótka zwłoka po starcie kontenera, żeby API zdążyło wstać.
    time.sleep(3)

    while True:
        collect_jellyfin_activity()
        time.sleep(JELLYFIN_COLLECT_INTERVAL)


def start_activity_collectors():
    global _activity_collectors_started

    with _activity_collectors_lock:
        if _activity_collectors_started:
            return False

        thread = threading.Thread(
            target=jellyfin_activity_loop,
            name="jellyfin-activity",
            daemon=True
        )
        thread.start()
        _activity_collectors_started = True

    return True
