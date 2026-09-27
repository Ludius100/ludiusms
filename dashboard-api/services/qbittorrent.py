import http.cookiejar
import json
import os
import urllib.parse
import urllib.request

from config import QBITTORRENT


def qb_client():
    username = os.environ["QBITTORRENT_USERNAME"]
    password = os.environ["QBITTORRENT_PASSWORD"]

    jar = http.cookiejar.CookieJar()

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )

    data = urllib.parse.urlencode({
        "username": username,
        "password": password
    }).encode()

    req = urllib.request.Request(
        QBITTORRENT + "/api/v2/auth/login",
        data=data,
        headers={
            "Origin": QBITTORRENT,
            "Referer": QBITTORRENT + "/"
        },
        method="POST"
    )

    with opener.open(req, timeout=5) as response:
        if response.status not in (200, 204):
            raise RuntimeError(
                f"qBittorrent login HTTP {response.status}"
            )

    if not list(jar):
        raise RuntimeError(
            "qBittorrent did not return a session cookie"
        )

    return opener


def qb_get(opener, path):
    req = urllib.request.Request(
        QBITTORRENT + path,
        headers={
            "Origin": QBITTORRENT,
            "Referer": QBITTORRENT + "/"
        }
    )

    with opener.open(req, timeout=5) as response:
        raw = response.read().decode()

    if not raw:
        return None

    return json.loads(raw)


def qb_post(opener, path, fields):
    data = urllib.parse.urlencode(fields).encode()

    req = urllib.request.Request(
        QBITTORRENT + path,
        data=data,
        headers={
            "Origin": QBITTORRENT,
            "Referer": QBITTORRENT + "/",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST"
    )

    with opener.open(req, timeout=10) as response:
        return response.status


def format_torrent(torrent):
    eta = torrent.get("eta", 0)

    # qBittorrent uses a very large value for unknown/infinite ETA.
    if not isinstance(eta, (int, float)) or eta < 0 or eta > 31_536_000:
        eta = None

    return {
        "hash": torrent.get("hash"),
        "name": torrent.get("name", ""),
        "state": torrent.get("state", ""),
        "progress": round(
            torrent.get("progress", 0) * 100,
            1
        ),
        "downloadSpeed": torrent.get("dlspeed", 0),
        "uploadSpeed": torrent.get("upspeed", 0),
        "downloaded": torrent.get("downloaded", 0),
        "uploaded": torrent.get("uploaded", 0),
        "size": torrent.get("size", 0),
        "eta": eta,
        "savePath": torrent.get("save_path", ""),
        "contentPath": torrent.get("content_path", "")
    }


def qb_find_torrent_by_magnet(opener, magnet):
    """
    Finds the torrent added from a magnet using its BTIH hash when possible.
    """
    parsed = urllib.parse.urlparse(magnet)
    params = urllib.parse.parse_qs(parsed.query)

    xt_values = params.get("xt", [])

    for xt in xt_values:
        prefix = "urn:btih:"

        if xt.lower().startswith(prefix):
            info_hash = xt[len(prefix):].strip().lower()

            # Standard hexadecimal BTIH.
            if len(info_hash) == 40:
                return info_hash

    return None


def qb_torrent_files(opener, torrent_hash):
    return qb_get(
        opener,
        "/api/v2/torrents/files?hash=" +
        urllib.parse.quote(torrent_hash)
    ) or []


def format_qb_file(item):
    name = item.get("name", "")
    lower = name.lower()

    video_exts = (
        ".mkv", ".mp4", ".avi", ".m4v",
        ".mov", ".ts", ".m2ts", ".webm"
    )

    subtitle_exts = (
        ".srt", ".ass", ".ssa", ".sub",
        ".vtt"
    )

    junk_exts = (
        ".nfo", ".jpg", ".jpeg", ".png",
        ".webp", ".txt"
    )

    is_sample = (
        "/sample/" in "/" + lower + "/" or
        lower.startswith("sample/") or
        "/sample." in lower or
        lower.startswith("sample.")
    )

    wanted = (
        lower.endswith(video_exts) or
        lower.endswith(subtitle_exts)
    )

    if lower.endswith(junk_exts) or is_sample:
        wanted = False

    return {
        "index": item.get("index"),
        "name": name,
        "size": item.get("size", 0),
        "progress": round(
            item.get("progress", 0) * 100,
            1
        ),
        "selected": wanted
    }
