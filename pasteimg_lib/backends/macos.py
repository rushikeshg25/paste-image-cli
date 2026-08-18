"""macOS clipboard access via osascript/sips -- no compilation, no extra installs.

AppleScript can coerce clipboard data to a type and write the raw bytes
straight to a file, so we never round-trip an image through hex text.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

from .base import IMAGE_FILE_SUFFIXES, BackendError, Clipboard

# AppleScript four-char clipboard classes, in preference order: the class code,
# the extension it produces, and the token `clipboard info` prints for it (which
# is *not* always the class code -- it says "GIF picture", not "GIFf").
# TIFF is what a macOS screenshot usually carries; we convert it to PNG after.
_CLASSES: list[tuple[str, str, str]] = [
    ("PNGf", "png", "PNGf"),
    ("JPEG", "jpg", "JPEG"),
    ("GIFf", "gif", "GIF"),
    ("TIFF", "tiff", "TIFF"),
]

_WRITE_SCRIPT = '''
set outFile to POSIX file "{path}"
set fh to open for access outFile with write permission
try
    set eof fh to 0
    write (the clipboard as {klass}) to fh
    close access fh
on error errMsg number errNum
    close access fh
    error errMsg number errNum
end try
'''


class MacOSClipboard(Clipboard):
    name = "macos"

    @classmethod
    def available(cls) -> bool:
        return sys.platform == "darwin" and cls._has("osascript")

    def _clipboard_info(self) -> str:
        """Raw output of `clipboard info` -- the list of types currently held."""
        proc = self._run(["osascript", "-e", "clipboard info"], check=False)
        if proc.returncode != 0:
            return ""
        return proc.stdout.decode("utf-8", "replace")

    def read_image(self) -> tuple[bytes, str] | None:
        info = self._clipboard_info()
        # Fail fast when there is plainly no image, so we don't shell out four
        # times just to collect four errors.
        if not any(token in info for _, _, token in _CLASSES):
            return None

        for klass, ext, token in _CLASSES:
            if token not in info:
                continue
            data = self._extract(klass)
            if data is None:
                continue
            if ext == "tiff":
                converted = self._tiff_to_png(data)
                if converted is not None:
                    return converted, "png"
                return data, "tiff"
            return data, ext
        return None

    def _extract(self, klass: str) -> bytes | None:
        """Coerce the clipboard to `klass` and return the bytes, or None if it won't coerce."""
        fd, tmp = tempfile.mkstemp(prefix="pasteimg-", suffix=".bin")
        os.close(fd)
        try:
            script = _WRITE_SCRIPT.format(path=tmp, klass=f"\u00abclass {klass}\u00bb")
            proc = self._run(["osascript", "-e", script], check=False)
            if proc.returncode != 0:
                return None
            data = Path(tmp).read_bytes()
            return data or None
        finally:
            Path(tmp).unlink(missing_ok=True)

    def _tiff_to_png(self, data: bytes) -> bytes | None:
        """Convert TIFF bytes to PNG with sips. Returns None if sips is unavailable or fails."""
        if not self._has("sips"):
            return None
        with tempfile.TemporaryDirectory(prefix="pasteimg-") as tmpdir:
            src = Path(tmpdir) / "in.tiff"
            dst = Path(tmpdir) / "out.png"
            src.write_bytes(data)
            proc = self._run(
                ["sips", "-s", "format", "png", str(src), "--out", str(dst)],
                check=False,
            )
            if proc.returncode != 0 or not dst.exists():
                return None
            return dst.read_bytes()

    def read_file_urls(self) -> list[str]:
        info = self._clipboard_info()
        if "furl" not in info:
            return []
        script = (
            'set out to ""\n'
            'try\n'
            '    set theItems to the clipboard as «class furl»\n'
            '    set out to POSIX path of theItems\n'
            'end try\n'
            'return out'
        )
        proc = self._run(["osascript", "-e", script], check=False)
        if proc.returncode != 0:
            return []
        raw = proc.stdout.decode("utf-8", "replace").strip()
        if not raw:
            return []
        paths = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("file://"):
                line = unquote(urlparse(line).path)
            if Path(line).suffix.lower() in IMAGE_FILE_SUFFIXES and Path(line).is_file():
                paths.append(line)
        return paths

    def write_text(self, text: str) -> None:
        self._run(["pbcopy"], stdin=text.encode("utf-8"))

    def notify(self, title: str, body: str) -> None:
        def esc(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')

        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{esc(body)}" with title "{esc(title)}"'],
                capture_output=True,
                check=False,
                timeout=5,
            )
        except Exception:
            pass  # notifications are decoration; never fail the paste over one
