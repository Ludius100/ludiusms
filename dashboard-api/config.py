import os


# ============================================================
# External services
# ============================================================

def _service_url(env_name, default):
    value = os.environ.get(env_name) or default
    return value.strip().rstrip("/")


def _optional_service_url(env_name):
    value = os.environ.get(env_name)

    if value is None or not value.strip():
        return None

    return value.strip().rstrip("/")


def _env_path(env_name, default):
    value = (os.environ.get(env_name) or default).strip()

    if value != "/":
        value = value.rstrip("/")

    return value


def _env_bool(env_name, default):
    value = os.environ.get(env_name)

    if value is None or not value.strip():
        return default

    normalized = value.strip().lower()

    if normalized in ("1", "true", "yes", "on"):
        return True

    if normalized in ("0", "false", "no", "off"):
        return False

    raise ValueError(
        f"{env_name} must be true/false, 1/0, yes/no or on/off"
    )


def _env_int(env_name, default):
    value = os.environ.get(env_name)

    if value is None or not value.strip():
        return default

    return int(value.strip())


def _env_mode(env_name, default):
    value = os.environ.get(env_name)

    if value is None or not value.strip():
        return default

    value = value.strip().lower()

    if value.startswith("0o"):
        value = value[2:]

    return int(value, 8)


ENABLE_JELLYFIN = _env_bool("ENABLE_JELLYFIN", True)
ENABLE_QBITTORRENT = _env_bool("ENABLE_QBITTORRENT", True)

HOMEPAGE_ORIGIN = _service_url(
    "HOMEPAGE_ORIGIN",
    "http://127.0.0.1:3000",
)

JELLYFIN = _service_url(
    "JELLYFIN_URL",
    "http://127.0.0.1:8096",
)
KEY_FILE = _env_path(
    "JELLYFIN_API_KEY_FILE",
    "/run/secrets/jellyfin_api_key",
)

QBITTORRENT = _service_url(
    "QBITTORRENT_URL",
    "http://127.0.0.1:8080",
)

GDRIVE = _optional_service_url("GDRIVE_URL")
KUMA = _optional_service_url("KUMA_URL")
NTFY = _optional_service_url("NTFY_URL")

SERVICE_STATUS_URLS = {}

if ENABLE_JELLYFIN:
    SERVICE_STATUS_URLS["jellyfin"] = JELLYFIN

for name, url in (
    ("gdrive", GDRIVE),
    ("kuma", KUMA),
    ("ntfy", NTFY),
):
    if url:
        SERVICE_STATUS_URLS[name] = url

if ENABLE_QBITTORRENT:
    SERVICE_STATUS_URLS["qbittorrent"] = QBITTORRENT


# ============================================================
# NAS filesystem
# ============================================================

NAS_ROOT = _env_path("NAS_ROOT", "/nas")
NAS_UID = _env_int("NAS_UID", 1002)
NAS_GID = _env_int("NAS_GID", 1003)
NAS_DIRECTORY_MODE = _env_mode("NAS_DIRECTORY_MODE", 0o2770)
NAS_FILE_MODE = _env_mode("NAS_FILE_MODE", 0o660)

LIBRARY_MOVIES_PATH = _env_path(
    "LIBRARY_MOVIES_PATH",
    os.path.join(NAS_ROOT, "Filmy"),
)
LIBRARY_SERIES_PATH = _env_path(
    "LIBRARY_SERIES_PATH",
    os.path.join(NAS_ROOT, "Seriale"),
)
LIBRARY_ANIME_PATH = _env_path(
    "LIBRARY_ANIME_PATH",
    os.path.join(NAS_ROOT, "Anime"),
)
LIBRARY_ANIME_MOVIES_PATH = _env_path(
    "LIBRARY_ANIME_MOVIES_PATH",
    os.path.join(NAS_ROOT, "Anime Filmy"),
)
LIBRARY_DOWNLOADS_PATH = _env_path(
    "LIBRARY_DOWNLOADS_PATH",
    os.path.join(NAS_ROOT, "Downloads"),
)


QBITTORRENT_LIBRARIES = {
    "movies": {
        "name": "Filmy",
        "path": LIBRARY_MOVIES_PATH,
    },
    "series": {
        "name": "Seriale",
        "path": LIBRARY_SERIES_PATH,
    },
    "anime": {
        "name": "Anime",
        "path": LIBRARY_ANIME_PATH,
    },
    "animeMovies": {
        "name": "Anime Filmy",
        "path": LIBRARY_ANIME_MOVIES_PATH,
    },
    "downloads": {
        "name": "Downloads",
        "path": LIBRARY_DOWNLOADS_PATH,
    },
}


# ============================================================
# Runtime state
# ============================================================

DATA_DIR = _env_path("LMS_DATA_DIR", "/app/data")

ACTIVITY_FILE = os.path.join(DATA_DIR, "activity.json")
ACTIVITY_LIMIT = 100

JELLYFIN_STATE_FILE = os.path.join(
    DATA_DIR,
    "jellyfin-state.json",
)
JELLYFIN_COLLECT_INTERVAL = 30


# ============================================================
# Local media upload
# ============================================================

LOCAL_MEDIA_LIBRARIES = {
    key: value
    for key, value in QBITTORRENT_LIBRARIES.items()
    if key in ("movies", "series", "anime", "animeMovies")
}

UPLOAD_STATE_DIR = os.path.join(
    DATA_DIR,
    "upload-sessions",
)
UPLOAD_STAGING_DIR = os.path.join(
    NAS_ROOT,
    ".uploads",
)
UPLOAD_CHUNK_MAX = 32 * 1024 * 1024


# ============================================================
# Media planner
# ============================================================

VIDEO_EXTENSIONS = (
    ".mkv", ".mp4", ".avi", ".m4v", ".mov", ".ts", ".m2ts", ".webm"
)

SUBTITLE_EXTENSIONS = (
    ".srt", ".ass", ".ssa", ".sub", ".vtt"
)

SUBTITLE_LANGUAGE_TAGS = {
    "pl", "pol", "pl-pl", "en", "eng", "en-us", "en-gb",
    "de", "ger", "deu", "fr", "fre", "fra", "es", "spa",
    "it", "ita", "ja", "jpn", "jp"
}
