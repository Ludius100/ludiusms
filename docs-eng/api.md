# LMS API

Ludius MS exposes its backend through a JSON HTTP API under `/api`.

The API is still part of the 0.x development line. Existing frontend behavior is preserved during refactors, but the public contract is not frozen yet.

## Discovery

### GET /api/health

Basic process health check.

Example response:

```json
{
  "status": "ok"
}
```

### GET /api/modules

Returns modules known to this LMS build and whether they are enabled.

Example:

```json
{
  "modules": {
    "jellyfin": {
      "name": "Jellyfin",
      "enabled": true,
      "apiPrefix": "/api/jellyfin"
    },
    "qbittorrent": {
      "name": "qBittorrent",
      "enabled": true,
      "apiPrefix": "/api/qbittorrent"
    }
  }
}
```

A disabled module remains discoverable in this manifest with `enabled: false`, but its module routes are not registered.

## Core API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/activity?limit=20` | Recent LMS activity. Limit is clamped to 1-100. |
| GET | `/api/system` | CPU, RAM, storage and uptime summary. |
| GET | `/api/status` | Reachability/latency for configured services. |
| GET | `/api/modules` | Module manifest. |
| GET | `/api/health` | Basic health check. |

Optional status services with no configured URL are omitted from `/api/status`.

## Jellyfin module

The following route exists only when the Jellyfin module is enabled.

### GET /api/jellyfin

Returns the LMS dashboard summary built from Jellyfin counts and sessions.

Current fields include:

- `online`
- `movies`
- `series`
- `episodes`
- `songs`
- `activeSessions`

An unavailable Jellyfin backend returns HTTP 503 with `online: false`.

## qBittorrent module

These routes exist only when the qBittorrent module is enabled.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/qbittorrent` | qBittorrent dashboard/status data. |
| GET | `/api/qbittorrent/libraries` | Available download targets. |
| POST | `/api/qbittorrent/add` | Prepare a magnet and return torrent/file information. |
| POST | `/api/qbittorrent/start` | Start a prepared torrent with selected file indexes. |

Prepare request:

```json
{
  "magnet": "magnet:?xt=...",
  "library": "downloads"
}
```

Start request:

```json
{
  "hash": "torrent-hash",
  "selected": [0, 1, 4]
}
```

The prepare/start flow intentionally separates metadata inspection from the mutation that starts the download.

## Media API

### GET /api/media/titles

Query:

- `library` — one of the configured local media library IDs

Returns the title folders found in that library.

### GET /api/media/last-episode

Query:

- `library`
- `title`
- `season` (defaults to 1)

Used by the frontend to determine the latest existing episode for a series/anime title.

### POST /api/media/plan

Builds a filesystem plan without moving or uploading files.

Common fields:

- `type` — `movie` or `series`
- `library`
- `title`
- `files` — array of file objects with at least `name`; `size` is also accepted

Movie plans may include `year`.

Series plans may include `season` and `firstEpisode`. Individual files may override `season` and `episode`.

Planner results include the target library, planned items, conflicts/checks, a `ready` flag, and a tree representation for the frontend.

The planner does not perform the final write itself.

## Chunked upload API

Large browser uploads use resumable server-side sessions.

### POST /api/media/upload/init

Creates an upload session.

Example request:

```json
{
  "library": "movies",
  "folder": "Example (2026)",
  "originalName": "example.mkv",
  "targetName": "Example (2026).mkv",
  "size": 123456789
}
```

Returns HTTP 201 with an `uploadId`, expected size, current received bytes and maximum chunk size.

### GET /api/media/upload/<upload_id>

Returns the current session state. The client can use `received` as the resume offset.

### POST /api/media/upload/<upload_id>/chunk

Uploads the next binary chunk.

Required header:

```text
X-Upload-Offset: <current server offset>
```

The server rejects an offset that does not match its current file size.

### POST /api/media/upload/<upload_id>/finalize

Finalizes a complete upload and moves it to the planned destination.

### DELETE /api/media/upload/<upload_id>

Cancels a session and removes its staged partial file.

### POST /api/media/upload

Small-file fallback/test uploader using `multipart/form-data`.

Current form fields:

- `file`
- `library`
- `folder`
- `targetName`

## Errors

Domain validation errors generally return a 4xx status with a JSON body containing:

```json
{
  "ok": false,
  "error": "..."
}
```

Conflicts such as an already existing target may return HTTP 409.

Unexpected backend failures normally return HTTP 500 or 503 depending on the endpoint.

## CORS and caching

The API applies the configured `HOMEPAGE_ORIGIN` globally.

Current allowed methods:

```text
GET, POST, DELETE, OPTIONS
```

Current allowed request headers:

```text
Content-Type, X-Upload-Offset
```

API responses currently send `Cache-Control: no-store`.

## Current route groups

The Flask application is assembled from Blueprints:

- core
- media
- Jellyfin module
- qBittorrent module

The module registry decides which optional module Blueprints and background collectors are loaded.
