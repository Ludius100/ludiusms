import json
import os
import time

from config import ACTIVITY_FILE, ACTIVITY_LIMIT


def load_activity():
    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

    except FileNotFoundError:
        pass

    except Exception as e:
        print(
            "Activity load error:",
            type(e).__name__,
            e,
            flush=True
        )

    return []


def save_activity(events):
    directory = os.path.dirname(ACTIVITY_FILE)
    os.makedirs(directory, exist_ok=True)

    temporary = ACTIVITY_FILE + ".tmp"

    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(
            events[:ACTIVITY_LIMIT],
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temporary, ACTIVITY_FILE)


def add_activity(event_type, title, detail=None, source=None):
    title = str(title or "").strip()

    if not title:
        return

    events = load_activity()

    event = {
        "id": str(time.time_ns()),
        "type": str(event_type),
        "title": title,
        "timestamp": int(time.time())
    }

    if detail:
        event["detail"] = str(detail)

    if source:
        event["source"] = str(source)

    events.insert(0, event)
    save_activity(events)
