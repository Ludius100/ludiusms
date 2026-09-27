import os


# ============================================================
# External services
# ============================================================

JELLYFIN = "http://127.0.0.1:8096"
KEY_FILE = "/run/secrets/jellyfin_api_key"

QBITTORRENT = os.environ.get(
    "QBITTORRENT_URL",
    "http://100.127.67.28:8080"
).rstrip("/")

QBITTORRENT_LIBRARIES = {
    "movies": {
        "name": "Filmy",
        "path": "/nas/Filmy"
    },
    "series": {
        "name": "Seriale",
        "path": "/nas/Seriale"
    },
    "anime": {
        "name": "Anime",
        "path": "/nas/Anime"
    },
    "animeMovies": {
        "name": "Anime Filmy",
        "path": "/nas/Anime Filmy"
    },
    "downloads": {
        "name": "Downloads",
        "path": "/nas/Downloads"
    }
}


# ============================================================
# Runtime state
# ============================================================

ACTIVITY_FILE = "/app/data/activity.json"
ACTIVITY_LIMIT = 100

JELLYFIN_STATE_FILE = "/app/data/jellyfin-state.json"
JELLYFIN_COLLECT_INTERVAL = 30


# ============================================================
# Local media upload
# ============================================================

LOCAL_MEDIA_LIBRARIES = {
    key: value
    for key, value in QBITTORRENT_LIBRARIES.items()
    if key in ("movies", "series", "anime", "animeMovies")
}

UPLOAD_STATE_DIR = "/app/data/upload-sessions"
UPLOAD_STAGING_DIR = "/nas/.uploads"
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
