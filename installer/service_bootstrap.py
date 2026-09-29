[Reading 284 lines from start (total: 284 lines, 0 remaining)]

#!/usr/bin/env python3
import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request


class ServiceBootstrapError(RuntimeError):
    pass


def _json_bytes(payload):
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _request(url, *, method="GET", headers=None, data=None, opener=None, timeout=8):
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers or {},
        method=method,
    )
    try:
        if opener is None:
            response = urllib.request.urlopen(
                request,
                timeout=timeout,
            )
        else:
            response = opener.open(
                request,
                timeout=timeout,
            )
        with response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()
        raise ServiceBootstrapError(
            f"HTTP {exc.code} dla {url}: {body[:300]!r}"
        ) from exc
def wait_http(base_url, path="/", *, timeout=120, interval=2):
    deadline = time.monotonic() + timeout
    url = base_url.rstrip("/") + path

    while time.monotonic() < deadline:
        try:
            status, _ = _request(url, timeout=3)
            if 200 <= status < 500:
                return True
        except (ServiceBootstrapError, urllib.error.URLError, TimeoutError):
            pass
        time.sleep(interval)

    raise ServiceBootstrapError(
        f"Usługa nie odpowiedziała w czasie: {base_url}"
    )


_QB_TEMP_PASSWORD_PATTERNS = (
    re.compile(
        r"temporary password is provided for this session:\s*(\S+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"temporary password.*?:\s*(\S+)",
        re.IGNORECASE,
    ),
)


def extract_qbittorrent_temp_password(log_text):
    for pattern in _QB_TEMP_PASSWORD_PATTERNS:
        match = pattern.search(log_text or "")
        if match:
            return match.group(1).strip()
    raise ServiceBootstrapError(
        "Nie znaleziono tymczasowego hasła qBittorrent w logu kontenera."
    )
def _qb_login(base_url, username, password):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )
    base = base_url.rstrip("/")
    form = urllib.parse.urlencode({
        "username": username,
        "password": password,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": base,
        "Referer": base + "/",
    }
    _, body = _request(
        base + "/api/v2/auth/login",
        method="POST",
        headers=headers,
        data=form,
        opener=opener,
    )
    if body.decode("utf-8", errors="replace").strip() != "Ok.":
        raise ServiceBootstrapError(
            "qBittorrent odrzucił dane logowania."
        )
    return opener


def qbittorrent_login_ok(base_url, username, password):
    try:
        _qb_login(base_url, username, password)
        return True
    except ServiceBootstrapError:
        return False


def qbittorrent_bootstrap(
    base_url,
    *,
    temporary_password,
    username,
    password,
    save_path="/nas/Downloads",
):
    base = base_url.rstrip("/")
    opener = _qb_login(base, "admin", temporary_password)
    preferences = {
        "web_ui_username": username,
        "web_ui_password": password,
        "save_path": save_path,
    }
    form = urllib.parse.urlencode({
        "json": json.dumps(preferences, separators=(",", ":"))
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": base,
        "Referer": base + "/",
    }
    _request(
        base + "/api/v2/app/setPreferences",
        method="POST",
        headers=headers,
        data=form,
        opener=opener,
    )

    # Verify the final credentials, not only the temporary session.
    _qb_login(base, username, password)
    return True


def _jellyfin_json(base_url, path, payload=None, *, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f'MediaBrowser Token="{token}"'
    data = _json_bytes(payload) if payload is not None else b""
    return _request(
        base_url.rstrip("/") + path,
        method=method,
        headers=headers,
        data=data if method != "GET" else None,
    )
def jellyfin_bootstrap(
    base_url,
    *,
    username,
    password,
    ui_culture="pl-PL",
    country_code="PL",
    metadata_language="pl",
):
    base = base_url.rstrip("/")
    wait_http(base, "/System/Info/Public", timeout=180)

    _jellyfin_json(
        base,
        "/Startup/Configuration",
        {
            "UICulture": ui_culture,
            "MetadataCountryCode": country_code,
            "PreferredMetadataLanguage": metadata_language,
        },
    )
    _jellyfin_json(
        base,
        "/Startup/User",
        {"Name": username, "Password": password},
    )
    _jellyfin_json(
        base,
        "/Startup/RemoteAccess",
        {
            "EnableRemoteAccess": True,
            "EnableAutomaticPortMapping": False,
        },
    )
    _jellyfin_json(base, "/Startup/Complete", {})
    return jellyfin_authenticate(base, username=username, password=password)
def jellyfin_authenticate(base_url, *, username, password):
    base = base_url.rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "X-Emby-Authorization": (
            'MediaBrowser Client="LMS Installer", '
            'Device="Server", DeviceId="lms-installer", Version="0.1"'
        ),
    }
    _, body = _request(
        base + "/Users/AuthenticateByName",
        method="POST",
        headers=headers,
        data=_json_bytes({
            "Username": username,
            "Pw": password,
        }),
    )
    try:
        payload = json.loads(body.decode("utf-8"))
        token = payload.get("AccessToken")
    except (UnicodeDecodeError, json.JSONDecodeError):
        token = None

    if not token:
        raise ServiceBootstrapError(
            "Jellyfin nie zwrócił tokenu po utworzeniu administratora."
        )
    return token
def jellyfin_token_ok(base_url, token):
    try:
        _jellyfin_json(
            base_url,
            "/System/Info",
            token=token,
            method="GET",
        )
        return True
    except ServiceBootstrapError:
        return False


def jellyfin_get_libraries(base_url, token):
    _, body = _jellyfin_json(
        base_url,
        "/Library/VirtualFolders",
        token=token,
        method="GET",
    )
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ServiceBootstrapError(
            "Nieprawidłowa odpowiedź listy bibliotek Jellyfin."
        ) from exc
    return data if isinstance(data, list) else []


def jellyfin_add_library(
    base_url,
    token,
    *,
    name,
    collection_type,
    paths,
):
    query = urllib.parse.urlencode(
        {
            "name": name,
            "collectionType": collection_type,
            "paths": list(paths),
            "refreshLibrary": "false",
        },
        doseq=True,
    )
    _jellyfin_json(
        base_url,
        "/Library/VirtualFolders?" + query,
        {},
        token=token,
        method="POST",
    )
    return True

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]