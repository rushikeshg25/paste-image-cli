"""Wayland clipboard access via wl-clipboard (`wl-paste` / `wl-copy`)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from .base import IMAGE_EXTENSIONS, IMAGE_FILE_SUFFIXES, Clipboard


class WaylandClipboard(Clipboard):
    name = "wayland"

    @classmethod
    def available(cls) -> bool:
        return (
            sys.platform.startswith("linux")
            and bool(os.environ.get("WAYLAND_DISPLAY"))
            and cls._has("wl-paste")
            and cls._has("wl-copy")
        )

    def _types(self) -> list[str]:
        proc = self._run(["wl-paste", "--list-types"], check=False)
        if proc.returncode != 0:
            return []
        return [t.strip() for t in proc.stdout.decode("utf-8", "replace").splitlines() if t.strip()]

    def read_image(self) -> tuple[bytes, str] | None:
        types = self._types()
        for mime, ext in IMAGE_EXTENSIONS.items():
            if mime not in types:
                continue
            proc = self._run(["wl-paste", "--no-newline", "--type", mime], check=False)
            if proc.returncode == 0 and proc.stdout:
                return proc.stdout, ext
        return None

    def read_file_urls(self) -> list[str]:
        if "text/uri-list" not in self._types():
            return []
        proc = self._run(["wl-paste", "--no-newline", "--type", "text/uri-list"], check=False)
        if proc.returncode != 0:
            return []
        return _parse_uri_list(proc.stdout.decode("utf-8", "replace"))

    def write_text(self, text: str) -> None:
        # wl-copy forks a clipboard-serving child. Do not capture output here:
        # that child inherits the pipes and would keep subprocess.run waiting
        # for EOF until something else replaces the clipboard.
        self._run(
            ["wl-copy", "--type", "text/plain"],
            stdin=text.encode("utf-8"),
            capture_output=False,
        )

    def notify(self, title: str, body: str) -> None:
        _notify_send(title, body)


def _parse_uri_list(raw: str) -> list[str]:
    """Extract local image paths from a text/uri-list payload."""
    paths = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("file://"):
            line = unquote(urlparse(line).path)
        p = Path(line)
        if p.suffix.lower() in IMAGE_FILE_SUFFIXES and p.is_file():
            paths.append(str(p))
    return paths


def _notify_send(title: str, body: str) -> None:
    """Best-effort desktop notification; silently does nothing without notify-send."""
    try:
        subprocess.run(["notify-send", title, body], capture_output=True, check=False, timeout=5)
    except Exception:
        pass
