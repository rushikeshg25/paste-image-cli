"""The platform-agnostic flow: grab an image off the clipboard, save it, report it.

Knows nothing about any specific OS -- it only talks to a `Clipboard` backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import store
from .backends import Clipboard, detect


class NoImageError(RuntimeError):
    """The clipboard has no image on it."""


@dataclass
class Grab:
    """What a successful clipboard grab produced."""

    path: Path
    size: int
    backend: str
    reused: bool  # True when we referenced an existing file instead of writing one

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "bytes": self.size,
            "backend": self.backend,
            "reused": self.reused,
        }


def grab(clipboard: Clipboard | None = None, *, prune_days: int = store.DEFAULT_PRUNE_DAYS) -> Grab:
    """Pull an image off the clipboard and return where it now lives on disk.

    Raises NoImageError if the clipboard holds no image, NoBackendError if no
    backend is usable, BackendError if a platform command fails.
    """
    cb = clipboard if clipboard is not None else detect()

    # An image file copied in a file manager is already on disk -- point at it
    # rather than making a second copy that then needs pruning.
    for candidate in cb.read_file_urls():
        path = Path(candidate)
        if path.is_file():
            return Grab(path=path, size=path.stat().st_size, backend=cb.name, reused=True)

    result = cb.read_image()
    if result is None:
        raise NoImageError("no image on the clipboard")

    data, ext = result
    path = store.save(data, ext)
    store.prune(prune_days)
    return Grab(path=path, size=len(data), backend=cb.name, reused=False)
