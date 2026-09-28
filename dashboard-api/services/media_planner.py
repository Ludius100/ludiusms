import os

from config import (
    LOCAL_MEDIA_LIBRARIES,
    SUBTITLE_EXTENSIONS,
    SUBTITLE_LANGUAGE_TAGS,
    VIDEO_EXTENSIONS,
)
from services.media_paths import path_is_inside, safe_media_component


class MediaPlannerError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            "ok": False,
            "error": message,
        }


def split_media_filename(name):
    clean = safe_media_component(
        os.path.basename(str(name or "").replace("\\", "/")),
        "media.bin"
    )
    stem, ext = os.path.splitext(clean)
    return clean, stem, ext.lower()


def subtitle_base_and_suffix(stem):
    """
    "episode.pol" -> ("episode", ".pol")
    "episode"     -> ("episode", "")
    """
    parts = stem.split(".")

    if len(parts) > 1 and parts[-1].lower() in SUBTITLE_LANGUAGE_TAGS:
        return ".".join(parts[:-1]), "." + parts[-1]

    return stem, ""


def planner_target(library, relative_parts):
    root = os.path.realpath(library["path"])
    target = os.path.join(root, *relative_parts)

    if not path_is_inside(target, root):
        raise MediaPlannerError("Nieprawidłowa ścieżka docelowa")

    return target


def planner_item(original, target_name, target_path, size=0, kind="other",
                 season=None, episode=None, paired_with=None):
    conflict = os.path.exists(target_path)

    result = {
        "originalName": original,
        "targetName": target_name,
        "targetPath": target_path,
        "size": int(size or 0),
        "kind": kind,
        "status": "conflict" if conflict else "ok",
        "conflict": conflict
    }

    if season is not None:
        result["season"] = int(season)

    if episode is not None:
        result["episode"] = int(episode)

    if paired_with is not None:
        result["pairedWith"] = paired_with

    return result


def plan_movie(data, library_id, library, files):
    if library_id not in ("movies", "animeMovies"):
        raise MediaPlannerError("Film może trafić tylko do Filmy lub Anime Filmy")

    title = safe_media_component(data.get("title", ""), "")
    if not title:
        raise MediaPlannerError("Podaj tytuł filmu")

    year = data.get("year")
    if year not in (None, ""):
        try:
            year = int(year)
        except (TypeError, ValueError):
            raise MediaPlannerError("Nieprawidłowy rok filmu")

        if year < 1888 or year > 2200:
            raise MediaPlannerError("Nieprawidłowy rok filmu")
    else:
        year = None

    folder = f"{title} ({year})" if year else title
    folder = safe_media_component(folder, title)

    planned = []

    for file_info in files:
        original, stem, ext = split_media_filename(file_info.get("name"))
        size = file_info.get("size", 0)

        if ext in VIDEO_EXTENSIONS:
            target_name = original
            kind = "video"
        elif ext in SUBTITLE_EXTENSIONS:
            target_name = original
            kind = "subtitle"
        else:
            target_name = original
            kind = "other"

        target_path = planner_target(library, [folder, target_name])
        planned.append(
            planner_item(
                original, target_name, target_path,
                size=size, kind=kind
            )
        )

    return {
        "mediaType": "movie",
        "title": title,
        "year": year,
        "folder": folder,
        "items": planned
    }


def plan_series(data, library_id, library, files):
    if library_id not in ("series", "anime"):
        raise MediaPlannerError("Serial może trafić tylko do Seriale lub Anime")

    title = safe_media_component(data.get("title", ""), "")
    if not title:
        raise MediaPlannerError("Podaj tytuł serialu")

    try:
        default_season = int(data.get("season", 1))
        first_episode = int(data.get("firstEpisode", 1))
    except (TypeError, ValueError):
        raise MediaPlannerError("Nieprawidłowy sezon lub numer pierwszego odcinka")

    if default_season < 0 or default_season > 999:
        raise MediaPlannerError("Nieprawidłowy numer sezonu")

    if first_episode < 0 or first_episode > 9999:
        raise MediaPlannerError("Nieprawidłowy numer pierwszego odcinka")

    videos = []
    subtitles = []
    ignored = []

    for position, file_info in enumerate(files):
        original, stem, ext = split_media_filename(file_info.get("name"))
        normalized = {
            "position": position,
            "original": original,
            "stem": stem,
            "ext": ext,
            "size": file_info.get("size", 0),
            "season": file_info.get("season"),
            "episode": file_info.get("episode")
        }

        if ext in VIDEO_EXTENSIONS:
            videos.append(normalized)
        elif ext in SUBTITLE_EXTENSIONS:
            subtitles.append(normalized)
        else:
            ignored.append(normalized)

    if not videos:
        raise MediaPlannerError("Nie znaleziono żadnego pliku wideo")

    # Numery odcinków nadajemy w kolejności przekazanej przez poczekalnię.
    for index, video in enumerate(videos):
        try:
            season = (
                int(video["season"])
                if video["season"] not in (None, "")
                else default_season
            )
            episode = (
                int(video["episode"])
                if video["episode"] not in (None, "")
                else first_episode + index
            )
        except (TypeError, ValueError):
            raise MediaPlannerError("Nieprawidłowy sezon lub numer odcinka przy pliku " + video["original"])

        if season < 0 or season > 999 or episode < 0 or episode > 9999:
            raise MediaPlannerError("Nieprawidłowy sezon lub numer odcinka przy pliku " + video["original"])

        video["targetSeason"] = season
        video["targetEpisode"] = episode

    planned = []
    video_by_stem = {video["stem"].lower(): video for video in videos}

    for video in videos:
        season = video["targetSeason"]
        episode = video["targetEpisode"]
        season_folder = f"Season {season:02d}"
        base = f"{title} S{season:02d}E{episode:02d}"
        target_name = base + video["ext"]
        target_path = planner_target(
            library,
            [title, season_folder, target_name]
        )

        planned.append(
            planner_item(
                video["original"], target_name, target_path,
                size=video["size"], kind="video",
                season=season, episode=episode
            )
        )

    # Napisy próbujemy przypisać po nazwie bazowej pliku.
    for subtitle in subtitles:
        base_stem, language_suffix = subtitle_base_and_suffix(subtitle["stem"])
        paired = video_by_stem.get(base_stem.lower())

        if paired is None:
            # Nie zgadujemy numeru odcinka. Poczekalnia pokaże "check".
            planned.append({
                "originalName": subtitle["original"],
                "targetName": None,
                "targetPath": None,
                "size": int(subtitle["size"] or 0),
                "kind": "subtitle",
                "status": "check",
                "conflict": False,
                "reason": "Nie udało się jednoznacznie przypisać napisów do odcinka"
            })
            continue

        season = paired["targetSeason"]
        episode = paired["targetEpisode"]
        season_folder = f"Season {season:02d}"
        base = f"{title} S{season:02d}E{episode:02d}"
        target_name = base + language_suffix + subtitle["ext"]
        target_path = planner_target(
            library,
            [title, season_folder, target_name]
        )

        planned.append(
            planner_item(
                subtitle["original"], target_name, target_path,
                size=subtitle["size"], kind="subtitle",
                season=season, episode=episode,
                paired_with=paired["original"]
            )
        )

    for item in ignored:
        planned.append({
            "originalName": item["original"],
            "targetName": None,
            "targetPath": None,
            "size": int(item["size"] or 0),
            "kind": "other",
            "status": "ignored",
            "conflict": False,
            "reason": "Nieobsługiwany typ pliku"
        })

    return {
        "mediaType": "series",
        "title": title,
        "season": default_season,
        "firstEpisode": first_episode,
        "folder": title,
        "items": planned
    }


def build_plan_tree(library, result):
    root = library["name"]
    paths = []

    for item in result["items"]:
        target = item.get("targetPath")
        if not target:
            continue

        relative = os.path.relpath(target, library["path"])
        paths.append(relative.replace(os.sep, "/"))

    return {
        "root": root,
        "paths": paths
    }


def create_media_plan(data):
    media_type = str(data.get("type", "")).strip().lower()
    library_id = str(data.get("library", "")).strip()
    library = LOCAL_MEDIA_LIBRARIES.get(library_id)
    files = data.get("files", [])

    if not library:
        raise MediaPlannerError(
            "Nieprawidłowa biblioteka lokalnych mediów"
        )

    if not isinstance(files, list) or not files:
        raise MediaPlannerError("Nie wybrano żadnych plików")

    if len(files) > 5000:
        raise MediaPlannerError(
            "Za dużo plików w jednym planie",
            status_code=413,
        )

    normalized_files = []

    for item in files:
        if not isinstance(item, dict):
            raise MediaPlannerError("Nieprawidłowa lista plików")

        name = str(item.get("name", "")).strip()

        if not name:
            raise MediaPlannerError("Jeden z plików nie ma nazwy")

        normalized_files.append(item)

    if media_type == "movie":
        result = plan_movie(
            data,
            library_id,
            library,
            normalized_files,
        )
    elif media_type == "series":
        result = plan_series(
            data,
            library_id,
            library,
            normalized_files,
        )
    else:
        raise MediaPlannerError("Typ musi być movie albo series")

    conflicts = sum(
        1
        for item in result["items"]
        if item.get("status") == "conflict"
    )
    checks = sum(
        1
        for item in result["items"]
        if item.get("status") == "check"
    )

    result.update({
        "ok": True,
        "library": library_id,
        "libraryName": library["name"],
        "conflicts": conflicts,
        "needsCheck": checks,
        "ready": conflicts == 0 and checks == 0,
        "tree": build_plan_tree(library, result),
    })

    return result
