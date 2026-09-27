# Configuration model

Ludius MS keeps three different kinds of configuration separate.

## 1. Secrets

Secrets are generated or entered locally during installation and must never be committed to Git.

Current secrets:

- Jellyfin API key
- qBittorrent username
- qBittorrent password

The future first-run wizard should write these values only to local configuration/secrets files.

## 2. Installation configuration

These values describe a particular Ludius MS installation and may differ between servers:

- timezone
- frontend/dashboard origin
- Jellyfin URL
- qBittorrent URL
- NAS host path
- media library paths

The repository contains only placeholders and defaults in `.env.example`.

## 3. Application/runtime constants

These are internal implementation details and should normally not be exposed in the first-run wizard:

- activity state file location
- Jellyfin collector state file location
- upload session directory
- upload staging directory
- upload chunk size
- activity history limit
- collector interval
- supported video/subtitle extensions

They belong in application configuration/code and can later be promoted to advanced settings only if there is a real need.

## First-run wizard direction

The public 0.x installer should ask only for values the user realistically needs to know:

1. server/network address or detected local address
2. timezone
3. Jellyfin URL and API key
4. qBittorrent URL, username and password
5. NAS/storage path
6. media library folders

The wizard should then generate the local `.env` and secret files, create required runtime directories, and validate connectivity before completing setup.
