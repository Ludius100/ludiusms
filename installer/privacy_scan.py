#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py", ".js", ".css", ".html", ".md", ".txt", ".yaml", ".yml",
    ".json", ".toml", ".ini", ".conf", ".sh", ".env",
}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", "tests"}
FORBIDDEN_NAMES = {".env", "qbittorrent.env", "jellyfin_api_key"}
GENERIC_PATTERNS = [
    ("OCI identifier", re.compile(r"\bocid1\.[A-Za-z0-9._-]+")),
    (
        "literal credential in code",
        re.compile(
            r"(?im)^\s*(?:password|token|api[_-]?key|secret)\s*=\s*"
            r"[\"'](?!<redacted>|example|changeme|test|<generated>)([^\"']{8,})[\"']\s*$"
        ),
    ),
]

CONFIG_SECRET_PATTERN = re.compile(
    r"(?m)^\s*[A-Z0-9_]*(?:PASSWORD|TOKEN|API_KEY|SECRET)[A-Z0-9_]*="
    r"(?!\$\{|\$\(|\{\{|<redacted>|example|changeme|test|<generated>)"
    r"[^\s#][^\r\n#]{7,}$"
)
CONFIG_SECRET_EXTENSIONS = {".env", ".ini", ".conf", ".yaml", ".yml", ".toml"}

IPV4_PATTERN = re.compile(
    r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])"
)
ALLOWED_LITERAL_IPS = {
    "0.0.0.0",
    "127.0.0.1",
    "169.254.169.254",
}


def _valid_ipv4(value):
    try:
        parts = [int(part) for part in value.split(".")]
    except ValueError:
        return False
    return len(parts) == 4 and all(0 <= part <= 255 for part in parts)


def load_deny_values(path):
    if not path:
        return []
    values = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            values.append(value)
    return values


def iter_files(root):
    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path
def scan(root, deny_values=None, allow_local_config=False):
    root = Path(root)
    deny_values = deny_values or []
    findings = []

    for path in iter_files(root):
        rel = path.relative_to(root)

        if not allow_local_config:
            if path.name in FORBIDDEN_NAMES or "secrets" in rel.parts:
                findings.append({
                    "path": str(rel),
                    "kind": "local config/secret file",
                    "match": path.name,
                })
                continue

        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name != ".env.example":
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for value in deny_values:
            if value in text:
                findings.append({
                    "path": str(rel),
                    "kind": "denylist value",
                    "match": value,
                })

        for label, pattern in GENERIC_PATTERNS:
            for match in pattern.finditer(text):
                findings.append({
                    "path": str(rel),
                    "kind": label,
                    "match": match.group(0)[:120],
                })

        for match in IPV4_PATTERN.finditer(text):
            ip = match.group(0)
            if (
                _valid_ipv4(ip)
                and ip not in ALLOWED_LITERAL_IPS
            ):
                findings.append({
                    "path": str(rel),
                    "kind": "hardcoded IPv4 address",
                    "match": ip,
                })

        if path.suffix.lower() in CONFIG_SECRET_EXTENSIONS:
            for match in CONFIG_SECRET_PATTERN.finditer(text):
                findings.append({
                    "path": str(rel),
                    "kind": "literal credential in config",
                    "match": match.group(0)[:120],
                })

    return findings
def main():
    parser = argparse.ArgumentParser(description="LMS build privacy scanner")
    parser.add_argument("path")
    parser.add_argument("--deny-file")
    parser.add_argument(
        "--allow-local-config",
        action="store_true",
        help="Allow .env/secrets when scanning a live install instead of a build tree.",
    )
    args = parser.parse_args()

    findings = scan(
        args.path,
        deny_values=load_deny_values(args.deny_file),
        allow_local_config=args.allow_local_config,
    )

    if not findings:
        print("privacy-scan: OK")
        return 0

    print(f"privacy-scan: FAIL ({len(findings)} finding(s))")
    for finding in findings:
        print(
            f"- {finding['path']}: {finding['kind']} -> {finding['match']}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
