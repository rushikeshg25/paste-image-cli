"""X11 clipboard access via xclip."""

from __future__ import annotations

import os
import sys

from .base import IMAGE_EXTENSIONS, Clipboard
from .wayland import _notify_send, _parse_uri_list


class X11Clipboard(Clipboard):
    name = "x11"

    @classmethod
    def available(cls) -> bool:
        return sys.platform.startswith("linux") and bool(os.environ.get("DISPLAY")) and cls._has("xclip")

    def _targets(self) -> list[str]:
        proc = self._run(["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"], check=False)
        if proc.returncode != 0:
            return []
        return [t.strip() for t in proc.stdout.decode("utf-8", "replace").splitlines() if t.strip()]

    def read_image(self) -> tuple[bytes, str] | None:
        targets = self._targets()
        for mime, ext in IMAGE_EXTENSIONS.items():
            if mime not in targets:
                continue
            proc = self._run(["xclip", "-selection", "clipboard", "-t", mime, "-o"], check=False)
            if proc.returncode == 0 and proc.stdout:
                return proc.stdout, ext
        return None

    def read_file_urls(self) -> list[str]:
        if "text/uri-list" not in self._targets():
            return []
        proc = self._run(["xclip", "-selection", "clipboard", "-t", "text/uri-list", "-o"], check=False)
        if proc.returncode != 0:
            return []
        return _parse_uri_list(proc.stdout.decode("utf-8", "replace"))

    def write_text(self, text: str) -> None:
        # xclip holds the selection until another owner takes it, so it must
        # outlive this process -- hence Popen rather than a blocking run.
        import subprocess

        proc = subprocess.Popen(
            ["xclip", "-selection", "clipboard", "-t", "text/plain"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        proc.stdin.write(text.encode("utf-8"))
        proc.stdin.close()

    def notify(self, title: str, body: str) -> None:
        _notify_send(title, body)
