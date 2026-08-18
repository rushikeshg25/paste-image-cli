"""Where saved clipboard images live, and how long they stay."""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

APP_DIR_NAME = "paste-cli-agent"
FILENAME_PREFIX = "clip-"
DEFAULT_PRUNE_DAYS = 7


def cache_dir() -> Path:
    """Image cache location. Honours XDG_CACHE_HOME; same code path on macOS and Linux."""
    base = os.environ.get("XDG_CACHE_HOME")
    root = Path(base) if base else Path.home() / ".cache"
    return root / APP_DIR_NAME


def save(data: bytes, ext: str) -> Path:
    """Write image bytes to a timestamped file and return its path."""
    directory = cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"{FILENAME_PREFIX}{stamp}.{ext}"
    # Two pastes inside the same second must not clobber each other.
    if path.exists():
        counter = 2
        while True:
            candidate = directory / f"{FILENAME_PREFIX}{stamp}-{counter}.{ext}"
            if not candidate.exists():
                path = candidate
                break
            counter += 1
    path.write_bytes(data)
    return path


def latest() -> Path | None:
    """Most recently saved image, or None if the cache is empty."""
    directory = cache_dir()
    if not directory.is_dir():
        return None
    files = [p for p in directory.iterdir() if p.is_file() and p.name.startswith(FILENAME_PREFIX)]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def prune(days: int = DEFAULT_PRUNE_DAYS) -> int:
    """Delete cached images older than `days`. Returns how many were removed.

    Only ever touches files this tool created (prefix-matched) inside its own
    cache dir. `days <= 0` disables pruning.
    """
    if days <= 0:
        return 0
    directory = cache_dir()
    if not directory.is_dir():
        return 0
    cutoff = time.time() - (days * 86400)
    removed = 0
    for path in directory.iterdir():
        if not path.is_file() or not path.name.startswith(FILENAME_PREFIX):
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            continue  # a file vanishing mid-prune is not worth failing over
    return removed
