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
