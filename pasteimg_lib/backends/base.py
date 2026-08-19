"""The seam between the platform-agnostic core and per-OS clipboard access.

Every platform implements `Clipboard`. `core.py` talks only to this interface,
so adding an OS means adding one module here plus one entry in the probe list
in `backends/__init__.py`.
"""

from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod


class BackendError(RuntimeError):
    """A platform command failed in a way the user needs to know about.

    Raised for genuine failures (missing tool, non-zero exit from a command we
    expected to work). An empty or image-less clipboard is *not* an error --
    `read_image` returns None for that.
    """


# Clipboard image types we know how to save, in preference order. PNG first:
# it is lossless and every agent reads it. The value is the file extension.
IMAGE_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/tiff": "tiff",
}

# File extensions we accept when the clipboard holds a file reference rather
# than raw bitmap data (an image copied in Finder or Nautilus).
IMAGE_FILE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tiff", ".tif", ".bmp", ".heic"}


class Clipboard(ABC):
    """Read images off the system clipboard and write text back to it."""

    name: str = "unknown"

    @classmethod
    @abstractmethod
    def available(cls) -> bool:
        """Whether this backend can run here (right OS, required tools present)."""

    @abstractmethod
    def read_image(self) -> tuple[bytes, str] | None:
        """Return (image_bytes, file_extension), or None if no image is on the clipboard."""

    @abstractmethod
    def read_file_urls(self) -> list[str]:
        """Return local filesystem paths for any files on the clipboard.

        Used to detect an image file copied from a file manager, which we can
        reference in place instead of duplicating into the cache.
        """

    @abstractmethod
    def write_text(self, text: str) -> None:
        """Replace the clipboard contents with plain text."""

    @abstractmethod
    def notify(self, title: str, body: str) -> None:
        """Show a desktop notification. Best effort -- never raises."""

    # -- helpers shared by every backend ---------------------------------

    @staticmethod
    def _has(binary: str) -> bool:
        return shutil.which(binary) is not None

    @staticmethod
    def _run(
        cmd: list[str],
        *,
        stdin: bytes | None = None,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        """Run a command and optionally capture bytes; wrap checked failures."""
        try:
            proc = subprocess.run(cmd, input=stdin, capture_output=capture_output, check=False)
        except FileNotFoundError as exc:
            raise BackendError(f"{cmd[0]} not found") from exc
        if check and proc.returncode != 0:
            detail = (
                proc.stderr.decode("utf-8", "replace").strip()
                if proc.stderr is not None
                else f"exit {proc.returncode}"
            )
            raise BackendError(f"{cmd[0]} failed: {detail}")
        return proc
