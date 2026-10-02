#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path


class HostOperationError(RuntimeError):
    pass


class HostOps:
    def __init__(self, *, enabled=False):
        self.enabled = bool(enabled)
        self.events = []

    def _event(self, action_id, kind, **details):
        event = {
            "action_id": action_id,
            "kind": kind,
            "status": "planned" if not self.enabled else "running",
            **details,
        }
        self.events.append(event)
        return event

    def run(self, argv, *, action_id, timeout=300):
        if not isinstance(argv, (list, tuple)) or not argv:
            raise HostOperationError("Nieprawidłowa komenda.")
        if any(not isinstance(part, str) or not part for part in argv):
            raise HostOperationError("Nieprawidłowy argument komendy.")

        event = self._event(action_id, "command", argv=list(argv))
        if not self.enabled:
            return event

        try:
            proc = subprocess.run(
                list(argv),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            event["status"] = "failed"
            event["error"] = str(exc)
            raise HostOperationError(str(exc)) from exc

        event["returncode"] = proc.returncode
        if proc.returncode != 0:
            event["status"] = "failed"
            event["stderr"] = proc.stderr[-4000:]
            raise HostOperationError(
                f"Komenda akcji {action_id} zakończyła się kodem {proc.returncode}."
            )

        event["status"] = "done"
        return event
    def ensure_dir(self, path, *, action_id, mode=0o755):
        path = Path(path)
        event = self._event(
            action_id, "mkdir", path=str(path), mode=oct(mode)
        )
        if self.enabled:
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(mode)
            event["status"] = "done"
        return event

    def write_text(self, path, text, *, action_id, mode=0o644, preserve_inode=False):
        path = Path(path)
        event = self._event(
            action_id,
            "write",
            path=str(path),
            mode=oct(mode),
            bytes=len(text.encode("utf-8")),
        )
        if self.enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            if preserve_inode and path.exists():
                # Docker single-file bind mounts keep the original inode.
                # Rewrite a mounted secret in place instead of replacing it.
                path.write_text(text, encoding="utf-8")
                path.chmod(mode)
            else:
                tmp = path.with_name(path.name + ".lms-tmp")
                tmp.write_text(text, encoding="utf-8")
                tmp.chmod(mode)
                os.replace(tmp, path)
            event["status"] = "done"
        return event

    def copy_file(self, source, destination, *, action_id, mode=None):
        source = Path(source)
        destination = Path(destination)
        if not source.is_file():
            raise HostOperationError(f"Brak pliku źródłowego: {source}")

        event = self._event(
            action_id,
            "copy",
            source=str(source),
            destination=str(destination),
        )
        if self.enabled:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            if mode is not None:
                destination.chmod(mode)
            event["status"] = "done"
        return event
    def append_line_once(self, path, line, *, action_id):
        path = Path(path)
        event = self._event(
            action_id,
            "append-once",
            path=str(path),
            line=line,
        )
        if self.enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            lines = current.splitlines()
            if line not in lines:
                with path.open("a", encoding="utf-8") as handle:
                    if current and not current.endswith("\n"):
                        handle.write("\n")
                    handle.write(line + "\n")
            event["status"] = "done"
        return event

    def chmod(self, path, mode, *, action_id):
        path = Path(path)
        event = self._event(
            action_id, "chmod", path=str(path), mode=oct(mode)
        )
        if self.enabled:
            path.chmod(mode)
            event["status"] = "done"
        return event

    def chown(self, path, uid, gid, *, action_id, recursive=False):
        path = Path(path)
        event = self._event(
            action_id,
            "chown",
            path=str(path),
            uid=int(uid),
            gid=int(gid),
            recursive=bool(recursive),
        )
        if self.enabled:
            if recursive and path.is_dir():
                os.chown(path, uid, gid)
                for child in path.rglob("*"):
                    os.chown(child, uid, gid)
            else:
                os.chown(path, uid, gid)
            event["status"] = "done"
        return event
    def copy_tree_whitelist(
        self,
        source,
        destination,
        *,
        action_id,
        files=(),
        directories=(),
    ):
        source = Path(source)
        destination = Path(destination)
        event = self._event(
            action_id,
            "copy-tree-whitelist",
            source=str(source),
            destination=str(destination),
            files=list(files),
            directories=list(directories),
        )

        for name in files:
            if not (source / name).is_file():
                raise HostOperationError(
                    f"Brak wymaganego pliku źródłowego: {source / name}"
                )
        for name in directories:
            if not (source / name).is_dir():
                raise HostOperationError(
                    f"Brak wymaganego katalogu źródłowego: {source / name}"
                )

        if self.enabled:
            destination.mkdir(parents=True, exist_ok=True)
            for name in files:
                shutil.copy2(source / name, destination / name)
            for name in directories:
                target = destination / name
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(
                    source / name,
                    target,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", "*.bak", "*.backup", "*.before-*"
                    ),
                )
            event["status"] = "done"
        return event
