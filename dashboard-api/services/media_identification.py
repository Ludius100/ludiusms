"""Safe, authenticated Jellyfin remote metadata lookup for the LMS title picker."""
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from config import ENABLE_JELLYFIN, JELLYFIN
from services.jellyfin import jellyfin_request


class IdentificationError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def _tmdb_id(result):
    for name, value in (result.get("ProviderIds") or {}).items():
        if re.sub(r"[^a-z]", "", name.lower()) in ("tmdb", "themoviedb"):
            candidate = str(value or "")
            if re.fullmatch(r"[1-9][0-9]{0,11}", candidate):
                return candidate
    return None


def _poster(url):
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
    except ValueError:
        return None
    if parsed.scheme == "https" and host == "image.tmdb.org":
        return url
    return None


def search_media(title, media_type, *, limit=12):
    if not ENABLE_JELLYFIN:
        raise IdentificationError("Jellyfin nie jest włączony w LMS")
    title = str(title or "").strip()
    if len(title) < 2 or len(title) > 150:
        raise IdentificationError("Wpisz tytuł (2–150 znaków)", 400)
    if media_type not in ("movie", "series"):
        raise IdentificationError("Nieobsługiwany typ mediów", 400)
    route = "Movie" if media_type == "movie" else "Series"
    payload = {"SearchInfo": {
        "Name": title, "MetadataLanguage": "pl", "MetadataCountryCode": "PL"
    }, "IncludeDisabledProviders": False}
    auth = jellyfin_request(f"/Items/RemoteSearch/{route}")
    request = urllib.request.Request(
        JELLYFIN + f"/Items/RemoteSearch/{route}",
        data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Authorization": auth.get_header("Authorization"),
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            results = json.load(response)
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        raise IdentificationError("Wyszukiwanie Jellyfin/TMDB jest niedostępne") from exc
    if not isinstance(results, list):
        raise IdentificationError("Nieprawidłowa odpowiedź wyszukiwarki Jellyfin")
    clean = []
    seen = set()
    for result in results:
        if not isinstance(result, dict):
            continue
        tmdb_id = _tmdb_id(result)
        if not tmdb_id or tmdb_id in seen:
            continue
        seen.add(tmdb_id)
        clean.append({"tmdbId": tmdb_id, "title": str(result.get("Name") or title)[:180],
                      "year": result.get("ProductionYear"), "poster": _poster(result.get("ImageUrl")),
                      "type": media_type})
        if len(clean) >= limit:
            break
    return {"ok": True, "results": clean}
