[Reading 42 lines from start (total: 42 lines, 0 remaining)]

#!/usr/bin/env bash
set -u

ok=0
warn=0
fail=0

pass(){ printf '[OK]   %s\n' "$1"; ok=$((ok+1)); }
warning(){ printf '[WARN] %s\n' "$1"; warn=$((warn+1)); }
failure(){ printf '[FAIL] %s\n' "$1"; fail=$((fail+1)); }

printf 'LMS Web - host preflight\n'
printf '%s\n' '------------------------'

if [ "$(uname -s)" = Linux ]; then pass 'Linux host'; else failure 'Linux is required'; fi

if [ -r /etc/os-release ]; then
  . /etc/os-release
  printf '       OS: %s\n' "${PRETTY_NAME:-unknown}"
  case "${ID:-}" in ubuntu|debian) pass 'Supported Debian-family OS';; *) warning 'OS has not been validated yet';; esac
else
  failure '/etc/os-release is unavailable'
fi

command -v docker >/dev/null 2>&1 && pass "Docker: $(docker --version 2>/dev/null)" || failure 'Docker is not installed'
docker compose version >/dev/null 2>&1 && pass "Compose: $(docker compose version 2>/dev/null)" || failure 'Docker Compose plugin is not available'
command -v curl >/dev/null 2>&1 && pass 'curl available' || failure 'curl is required'
command -v lsblk >/dev/null 2>&1 && pass 'lsblk available' || failure 'lsblk is required for storage discovery'

if docker info >/dev/null 2>&1; then pass 'Current user can access Docker'; else warning 'Current user cannot access Docker without elevation'; fi

mem_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
if [ "$mem_kb" -ge 1900000 ]; then pass "RAM: $((mem_kb/1024)) MiB"; else warning "RAM: $((mem_kb/1024)) MiB - test build target is >= 2 GiB"; fi

root_free_kb=$(df -Pk / | awk 'NR==2 {print $4}')
if [ "${root_free_kb:-0}" -ge 10485760 ]; then pass "Root free space: $((root_free_kb/1024/1024)) GiB"; else warning 'Less than 10 GiB free on root filesystem'; fi

printf '\nStorage candidates:\n'
lsblk -dnpo NAME,SIZE,TYPE,FSTYPE 2>/dev/null | awk '$3=="disk" {printf "  - %s  %s  %s\n",$1,$2,($4==""?"unformatted":$4)}'

printf '\nSummary: %d OK, %d warning(s), %d failure(s)\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]