# Configuration model

Ludius MS separates repository defaults, installation configuration, secrets, and runtime state.

## Local configuration and Git

The repository contains a root `.env.example` only as a template.

For the current Docker Compose layout:

1. copy the repository `.env.example` to `dashboard-api/.env`
2. adjust values for the local server
3. keep the real `.env` local

`.env`, `secrets/`, runtime data, partial uploads, and local backups are ignored by Git.

## 1. Modules

Current optional modules:

- Jellyfin
- qBittorrent

They are controlled with:

```env
ENABLE_JELLYFIN=true
ENABLE_QBITTORRENT=true
```

A disabled module is not registered in the LMS API. Its route is absent and its module-specific background work is not started.

The current module manifest is available from:

```text
GET /api/modules
```

This lets the frontend discover supported modules without guessing from 404 responses.

## 2. API runtime and frontend access

Important values:

- `LMS_BIND` — address and port used by Gunicorn
- `LMS_WORKERS` — Gunicorn worker count
- `LMS_THREADS` — threads per worker
- `HOMEPAGE_ORIGIN` — frontend origin allowed by CORS
- `TZ` — container timezone

The Docker image does not contain installation-specific IP addresses. Network addresses belong to the local `.env`.

## 3. Service endpoints

Main module endpoints:

- `JELLYFIN_URL`
- `QBITTORRENT_URL`

Optional status-only services:

- `GDRIVE_URL`
- `KUMA_URL`
- `NTFY_URL`

If an optional status URL is blank, that service is omitted from `GET /api/status`.

## 4. Secrets

Secrets must never be committed to Git.

### Jellyfin

The Jellyfin API key is stored as a local file.

- `JELLYFIN_API_KEY_HOST_PATH` — path on the host
- `JELLYFIN_API_KEY_FILE` — mounted path inside dashboard-api

### qBittorrent

qBittorrent credentials are stored in:

```text
dashboard-api/secrets/qbittorrent.env
```

with:

```env
QBITTORRENT_USERNAME=...
QBITTORRENT_PASSWORD=...
```

The Compose service loads this file separately from normal installation configuration.

## 5. Storage and permissions

`NAS_HOST_PATH` is the storage path on the host.

`NAS_ROOT` is the same storage as seen inside dashboard-api.

Example:

```env
NAS_HOST_PATH=/srv/storage/NAS
NAS_ROOT=/nas
```

LMS-created media uses centrally configured ownership and modes:

- `NAS_UID`
- `NAS_GID`
- `NAS_DIRECTORY_MODE`
- `NAS_FILE_MODE`

Media libraries can be overridden independently:

- `LIBRARY_MOVIES_PATH`
- `LIBRARY_SERIES_PATH`
- `LIBRARY_ANIME_PATH`
- `LIBRARY_ANIME_MOVIES_PATH`
- `LIBRARY_DOWNLOADS_PATH`

Blank library values fall back to the current Ludius MS folder layout below `NAS_ROOT`.

## 6. Runtime state

Persistent LMS state is mounted separately from media storage:

- `LMS_DATA_HOST_PATH` — host directory
- `LMS_DATA_DIR` — path inside dashboard-api

It contains state such as activity history, Jellyfin collector state, and upload sessions.

Implementation constants such as upload chunk size, activity history limit, collector interval, and supported media extensions remain application-level settings.

## First-run wizard direction

The future installer should generate local configuration rather than modify Python files. It should collect network settings, enabled modules, service credentials/endpoints, storage paths, and permissions; create required files/directories; then validate connectivity before completing setup.
