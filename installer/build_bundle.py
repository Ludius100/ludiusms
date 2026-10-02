#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from frontend_prepare import prepare_custom_js
from privacy_scan import load_deny_values, scan


API_FILES = ("Dockerfile", "app.py", "config.py", "gunicorn.conf.py")
API_DIRS = ("services", "routes", "modules")
INSTALLER_SKIP = {"__pycache__", "tests"}
COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    "*.bak",
    "*.backup",
    "*.before-*",
    "*.orig",
    "*.final-backup",
    ".env",
    "secrets",
    "data",
)


class BundleBuildError(RuntimeError):
    pass


def _copy_file(source, destination):
    if not source.is_file():
        raise BundleBuildError(f"Brak wymaganego pliku: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_api(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name in API_FILES:
        _copy_file(source / name, destination / name)

    for name in API_DIRS:
        src = source / name
        dst = destination / name
        if not src.is_dir():
            raise BundleBuildError(f"Brak katalogu API: {src}")
        shutil.copytree(src, dst, ignore=COPY_IGNORE)


def _copy_installer(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in INSTALLER_SKIP:
            continue
        if item.name.startswith("."):
            continue

        target = destination / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                target,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                ),
            )
        elif item.is_file():
            shutil.copy2(item, target)


def _copy_homepage(source, destination):
    source_js = source / "custom.js"
    source_css = source / "custom.css"
    if not source_js.is_file() or not source_css.is_file():
        raise BundleBuildError("Brak custom.js/custom.css Homepage.")

    destination.mkdir(parents=True, exist_ok=True)
    prepared = prepare_custom_js(
        source_js.read_text(encoding="utf-8")
    )
    (destination / "custom.js").write_text(
        prepared,
        encoding="utf-8",
    )
    shutil.copy2(source_css, destination / "custom.css")
    assets = source / "assets"
    if not assets.is_dir():
        assets = source.parent / "assets"
    for name in ("lms-logo.webp", "lms-hero.webp"):
        _copy_file(assets / name, destination / "assets" / name)


def _write_root_installer(root):
    path = root / "install.sh"
    content = r"""#!/usr/bin/env bash
set -euo pipefail

if [[ "@@EUID" -ne 0 ]]; then
    exec sudo "@@0" "@@@"
fi

ROOT="@@(cd -- "@@(dirname -- "@@{BASH_SOURCE[0]}")" && pwd)"

if [[ "@@{1:-}" == "--local" ]]; then
    export LMS_SETUP_TRANSPORT=local
    export LMS_BOOTSTRAP_TAILSCALE=0
    shift
else
    export LMS_SETUP_TRANSPORT="@@{LMS_SETUP_TRANSPORT:-auto}"
    export LMS_BOOTSTRAP_TAILSCALE="@@{LMS_BOOTSTRAP_TAILSCALE:-1}"
fi

export LMS_EXECUTION_READY=1
export LMS_ALLOW_CHANGES=1

exec "@@ROOT/installer/install.sh" "@@@"
""".replace("@@", "$")
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _write_build_info(root):
    payload = {
        "schema": 1,
        "product": "LMS",
        "channel": "test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (root / "BUILD_INFO.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_manifest(root):
    lines = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "MANIFEST.sha256":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(
            f"{digest}  {path.relative_to(root).as_posix()}"
        )
    (root / "MANIFEST.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def build_bundle(
    *,
    installer_source,
    api_source,
    homepage_source,
    output,
    deny_file=None,
):
    installer_source = Path(installer_source).resolve()
    api_source = Path(api_source).resolve()
    homepage_source = Path(homepage_source).resolve()
    output = Path(output).resolve()

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    _copy_installer(installer_source, output / "installer")
    _copy_api(api_source, output / "dashboard-api")
    _copy_homepage(homepage_source, output / "homepage")
    _write_root_installer(output)
    _write_build_info(output)
    _write_manifest(output)

    findings = scan(
        output,
        deny_values=load_deny_values(deny_file),
    )
    if findings:
        shutil.rmtree(output)
        summary = "; ".join(
            f"{item['path']}: {item['kind']}"
            for item in findings[:8]
        )
        raise BundleBuildError(
            "Privacy gate odrzucił bundle: " + summary
        )

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Build a self-contained LMS test bundle."
    )
    parser.add_argument("--installer-source", required=True)
    parser.add_argument("--api-source", required=True)
    parser.add_argument("--homepage-source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--deny-file")
    args = parser.parse_args()

    root = build_bundle(
        installer_source=args.installer_source,
        api_source=args.api_source,
        homepage_source=args.homepage_source,
        output=args.output,
        deny_file=args.deny_file,
    )
    print(f"bundle: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
