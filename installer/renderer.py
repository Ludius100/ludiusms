[Reading 231 lines from start (total: 231 lines, 0 remaining)]

#!/usr/bin/env python3

def _bool(value):
    return "true" if value else "false"


def _service_url(config, service_id, managed_name, port):
    plan = config["services"][service_id]
    if plan == "install":
        return f"http://{managed_name}:{port}"
    if plan == "existing":
        return f"http://host.docker.internal:{port}"
    return ""


def render_compose_env(plan, *, uid, gid, bind_address, allowed_hosts, timezone="Europe/Warsaw"):
    storage = plan["config"]["storage"]
    lines = [
        f"TZ={timezone}",
        f"LMS_UID={int(uid)}",
        f"LMS_GID={int(gid)}",
        f"LMS_BIND_ADDRESS={bind_address}",
        f"LMS_ALLOWED_HOSTS={allowed_hosts}",
        f"LMS_MEDIA_ROOT={storage['media_root']}",
    ]
    return "\n".join(lines) + "\n"


def render_app_env(plan, *, uid, gid, timezone="Europe/Warsaw"):
    config = plan["config"]
    services = config["services"]
    lines = [
        f"TZ={timezone}",
        "LMS_BIND=0.0.0.0:8090",
        "LMS_WORKERS=1",
        "LMS_THREADS=4",
        "HOMEPAGE_ORIGIN=http://lms-gateway:3000",
        f"ENABLE_JELLYFIN={_bool(services['jellyfin'] != 'skip')}",
        f"ENABLE_QBITTORRENT={_bool(services['qbittorrent'] != 'skip')}",
        f"JELLYFIN_URL={_service_url(config, 'jellyfin', 'lms-jellyfin', 8096)}",
        "JELLYFIN_API_KEY_FILE=/run/secrets/jellyfin_api_key",
        f"QBITTORRENT_URL={_service_url(config, 'qbittorrent', 'lms-qbittorrent', 8080)}",
        "NAS_ROOT=/nas",
        f"NAS_UID={int(uid)}",
        f"NAS_GID={int(gid)}",
        "NAS_DIRECTORY_MODE=2770",
        "NAS_FILE_MODE=0660",
        "LMS_DATA_DIR=/app/data",
    ]

    selected = set(config["libraries"])
    library_env = {
        "LIBRARY_MOVIES_PATH": "/nas/Filmy" if "movies" in selected else "",
        "LIBRARY_SERIES_PATH": "/nas/Seriale" if "series" in selected else "",
        "LIBRARY_ANIME_PATH": "/nas/Anime/Seriale" if "anime" in selected else "",
        "LIBRARY_ANIME_MOVIES_PATH": "/nas/Anime/Filmy" if "anime" in selected else "",
        "LIBRARY_DOWNLOADS_PATH": "/nas/Downloads",
    }
    lines.extend(f"{key}={value}" for key, value in library_env.items())
    return "\n".join(lines) + "\n"


def render_caddyfile():
    return """:3000 {
    handle /api/* {
        reverse_proxy lms-api:8090
    }

    handle {
        reverse_proxy lms-homepage:3000 {
            header_up Host lms-homepage:3000
        }
    }
}
"""


def render_homepage_settings():
    return """title: LMS
language: pl
theme: dark
color: slate
headerStyle: clean
hideVersion: true
useEqualHeights: true
"""


def render_empty_yaml():
    return "[]\n"
def _compose_header():
    return """services:
  gateway:
    image: caddy:2-alpine
    container_name: lms-gateway
    restart: unless-stopped
    ports:
      - "${LMS_BIND_ADDRESS}:3000:3000"
    volumes:
      - ./gateway/Caddyfile:/etc/caddy/Caddyfile:ro
    networks:
      - lms

  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    container_name: lms-homepage
    restart: unless-stopped
    expose:
      - "3000"
    volumes:
      - ./homepage/config:/app/config
    environment:
      HOMEPAGE_ALLOWED_HOSTS: "${LMS_ALLOWED_HOSTS}"
      PUID: "${LMS_UID}"
      PGID: "${LMS_GID}"
      TZ: "${TZ}"
    networks:
      - lms

"""
def _dashboard_api_service(config):
    env_files = ["      - ./config/lms.env"]
    volumes = [
        '      - "${LMS_MEDIA_ROOT}:/nas"',
        "      - ./data:/app/data",
    ]

    if config["services"]["qbittorrent"] != "skip":
        env_files.append("      - ./secrets/qbittorrent.env")
    if config["services"]["jellyfin"] != "skip":
        volumes.append(
            "      - ./secrets/jellyfin_api_key:/run/secrets/jellyfin_api_key:ro"
        )

    return """  dashboard-api:
    build:
      context: ./dashboard-api
    container_name: lms-api
    restart: unless-stopped
    user: "${LMS_UID}:${LMS_GID}"
    expose:
      - "8090"
    env_file:
%s
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
%s
    networks:
      - lms

""" % ("\n".join(env_files), "\n".join(volumes))
def _jellyfin_service():
    return """  jellyfin:
    image: jellyfin/jellyfin:12.1
    container_name: lms-jellyfin
    restart: unless-stopped
    user: "${LMS_UID}:${LMS_GID}"
    ports:
      - "${LMS_BIND_ADDRESS}:8096:8096/tcp"
      - "${LMS_BIND_ADDRESS}:7359:7359/udp"
    volumes:
      - ./jellyfin/config:/config
      - ./jellyfin/cache:/cache
      - "${LMS_MEDIA_ROOT}:/media"
    networks:
      - lms

"""


def _qbittorrent_service():
    return """  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: lms-qbittorrent
    restart: unless-stopped
    ports:
      - "${LMS_BIND_ADDRESS}:8080:8080/tcp"
      - "6881:6881/tcp"
      - "6881:6881/udp"
    environment:
      PUID: "${LMS_UID}"
      PGID: "${LMS_GID}"
      TZ: "${TZ}"
      WEBUI_PORT: "8080"
    volumes:
      - ./qbittorrent/config:/config
      - "${LMS_MEDIA_ROOT}:/nas"
    networks:
      - lms

"""
def render_compose(plan):
    config = plan["config"]
    parts = [_compose_header(), _dashboard_api_service(config)]

    if config["services"]["jellyfin"] == "install":
        parts.append(_jellyfin_service())
    if config["services"]["qbittorrent"] == "install":
        parts.append(_qbittorrent_service())

    parts.append("""networks:
  lms:
    name: lms
""")
    return "".join(parts)


def render_bundle(plan, *, uid, gid, bind_address, allowed_hosts, timezone="Europe/Warsaw"):
    return {
        "compose.yaml": render_compose(plan),
        ".env": render_compose_env(
            plan,
            uid=uid,
            gid=gid,
            bind_address=bind_address,
            allowed_hosts=allowed_hosts,
            timezone=timezone,
        ),
        "config/lms.env": render_app_env(
            plan,
            uid=uid,
            gid=gid,
            timezone=timezone,
        ),
        "gateway/Caddyfile": render_caddyfile(),
        "homepage/config/settings.yaml": render_homepage_settings(),
        "homepage/config/services.yaml": render_empty_yaml(),
        "homepage/config/widgets.yaml": render_empty_yaml(),
        "homepage/config/bookmarks.yaml": render_empty_yaml(),
    }

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]