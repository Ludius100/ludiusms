#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PORT="${LMS_SETUP_PORT:-8765}"
TOKEN="${LMS_SETUP_TOKEN:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')}"
TRANSPORT="${LMS_SETUP_TRANSPORT:-auto}"
HOST="${LMS_SETUP_BIND:-}"
export LMS_SETUP_TOKEN="$TOKEN"

tailscale_ip() {
    command -v tailscale >/dev/null 2>&1 || return 1
    local ip
    ip="$(tailscale ip -4 2>/dev/null | head -n1 || true)"
    [[ -n "$ip" ]] || return 1
    printf '%s' "$ip"
}

bootstrap_tailscale() {
    [[ "$EUID" -eq 0 ]] || return 1

    local os_id="" codename=""
    if [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        os_id="${ID:-}"
        codename="${VERSION_CODENAME:-}"
    fi

    if [[ "$os_id" != "ubuntu" || ! "$codename" =~ ^(noble|jammy)$ ]]; then
        printf 'Automatic Tailscale bootstrap currently supports Ubuntu 22.04/24.04 only.\n'
        return 1
    fi

    printf 'Installing Tailscale for secure LMS Setup access...\n'
    apt-get update
    apt-get install -y curl ca-certificates
    install -d -m 0755 /usr/share/keyrings

    curl -fsSL         "https://pkgs.tailscale.com/stable/ubuntu/${codename}.noarmor.gpg"         -o /usr/share/keyrings/tailscale-archive-keyring.gpg

    curl -fsSL         "https://pkgs.tailscale.com/stable/ubuntu/${codename}.tailscale-keyring.list"         -o /etc/apt/sources.list.d/tailscale.list

    apt-get update
    apt-get install -y tailscale
    systemctl enable --now tailscaled
}

choose_setup_host() {
    if [[ -n "$HOST" ]]; then
        return
    fi

    if [[ "$TRANSPORT" == "local" ]]; then
        HOST="127.0.0.1"
        return
    fi

    local ip=""
    ip="$(tailscale_ip || true)"
    if [[ -n "$ip" ]]; then
        HOST="$ip"
        return
    fi

    if [[ "${LMS_BOOTSTRAP_TAILSCALE:-0}" == "1" ]]; then
        if ! command -v tailscale >/dev/null 2>&1; then
            bootstrap_tailscale || true
        fi

        if command -v tailscale >/dev/null 2>&1; then
            printf '\nTailscale needs authorization before graphical setup.\n'
            printf 'Open the login URL printed below in your browser.\n\n'

            if tailscale up; then
                ip="$(tailscale_ip || true)"
            fi

            if [[ -n "$ip" ]]; then
                HOST="$ip"
                return
            fi
        fi
    fi

    HOST="127.0.0.1"
}

choose_setup_host

printf 'LMS Web Setup (test build)\n'
printf '%s\n' '--------------------------'
"$ROOT/check-host.sh" || true

printf '\nGraphical setup: http://%s:%s/?token=%s\n' "$HOST" "$PORT" "$TOKEN"
printf 'Keep this setup URL private. It is valid only for this setup process.\n'

if [[ "$HOST" == "127.0.0.1" ]]; then
    printf '\nSetup is bound to localhost. From your computer, create an SSH tunnel:\n'
    printf '  ssh -L %s:127.0.0.1:%s <your-server>\n' "$PORT" "$PORT"
    printf 'Then open the Graphical setup URL above on your computer.\n'
fi

ARGS=(--bind "$HOST" --port "$PORT")
if [[ "${LMS_ALLOW_CHANGES:-0}" == "1" ]]; then
    ARGS+=(--allow-changes)
fi

exec python3 "$ROOT/setup_server.py" "${ARGS[@]}"
