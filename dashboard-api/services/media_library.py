import os
import re

from config import LOCAL_MEDIA_LIBRARIES, VIDEO_EXTENSIONS
from services.media_paths import path_is_inside


MEDIA_LIBRARY_IDS = ("movies", "animeMovies", "series", "anime")
SERIES_LIBRARY_IDS = ("series", "anime")

EPISODE_PATTERN = re.compile(
    r"(?i)(?:^|[^A-Z0-9])S(\d{1,3})E(\d{1,4})(?:[^0-9]|$)"
)


class MediaLibraryError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            "ok": False,
            "error": message,
        }


def _get_library(library_id, allowed_ids, error_message):
    library_id = str(library_id or "").strip()
    library = LOCAL_MEDIA_LIBRARIES.get(library_id)

    if library_id not in allowed_ids or not library:
        raise MediaLibraryError(error_message)

    return library_id, library


def get_media_titles(library_id):
    library_id, library = _get_library(
        library_id,
        MEDIA_LIBRARY_IDS,
        "Nieprawidłowa biblioteka lokalnych mediów",
    )
    root = os.path.realpath(library["path"])
    titles = []

    if os.path.isdir(root):
        with os.scandir(root) as entries:
            for entry in entries:
                if entry.name.startswith("."):
                    continue

                try:
                    if entry.is_dir(follow_symlinks=False):
                        titles.append(entry.name)
                except OSError:
                    continue

    titles.sort(key=lambda value: value.casefold())

    return {
        "ok": True,
        "library": library_id,
        "libraryName": library["name"],
        "titles": titles,
    }


def _find_title_directory(library_root, title):
    if not os.path.isdir(library_root):
        return None

    with os.scandir(library_root) as entries:
        for entry in entries:
            try:
                if (
                    entry.is_dir(follow_symlinks=False)
                    and entry.name.casefold() == title.casefold()
                ):
                    return os.path.realpath(entry.path)
            except OSError:
                continue

    return None


def _find_last_episode(title_dir, season):
    highest_episode = None
    highest_file = None

    for current_root, dirs, files in os.walk(title_dir):
        dirs[:] = [directory for directory in dirs if not directory.startswith(".")]

        for filename in files:
            extension = os.path.splitext(filename)[1].lower()

            if extension not in VIDEO_EXTENSIONS:
                continue

            match = EPISODE_PATTERN.search(filename)

            if not match:
                continue

            file_season = int(match.group(1))
            episode = int(match.group(2))

            if file_season != season:
                continue

            if highest_episode is None or episode > highest_episode:
                highest_episode = episode
                highest_file = filename

    return highest_episode, highest_file


def get_last_episode(library_id, title, season=1):
    library_id, library = _get_library(
        library_id,
        SERIES_LIBRARY_IDS,
        "Nieprawidłowa biblioteka seriali",
    )
    title = str(title or "").strip()

    if not title:
        raise MediaLibraryError("Brak tytułu")

    try:
        season = int(season)
    except (TypeError, ValueError):
        raise MediaLibraryError("Nieprawidłowy sezon")

    library_root = os.path.realpath(library["path"])
    title_dir = _find_title_directory(library_root, title)

    if title_dir is None:
        return {
            "ok": True,
            "exists": False,
            "season": season,
            "lastEpisode": None,
            "nextEpisode": 1,
        }

    if not path_is_inside(title_dir, library_root):
        raise MediaLibraryError("Nieprawidłowa ścieżka tytułu")

    highest_episode, highest_file = _find_last_episode(title_dir, season)

    return {
        "ok": True,
        "exists": True,
        "season": season,
        "lastEpisode": highest_episode,
        "lastFile": highest_file,
        "nextEpisode": (
            highest_episode + 1
            if highest_episode is not None
            else 1
        ),
    }
