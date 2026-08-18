"""Backend registry: probe the platform and hand back a usable Clipboard.

To support a new platform, add a module here and append its class to `_PROBE`.
Nothing in `core.py` changes.
"""

from __future__ import annotations

import sys

from .base import BackendError, Clipboard
from .macos import MacOSClipboard
from .wayland import WaylandClipboard
from .x11 import X11Clipboard

# Order matters: on Linux, Wayland is checked before X11 so that a session
# running XWayland doesn't get routed through xclip.
_PROBE: list[type[Clipboard]] = [MacOSClipboard, WaylandClipboard, X11Clipboard]


class NoBackendError(RuntimeError):
    """No clipboard backend is usable here. Message explains how to fix it."""


def detect() -> Clipboard:
    for cls in _PROBE:
        if cls.available():
            return cls()
    raise NoBackendError(_diagnose())


def _diagnose() -> str:
    """Explain what is missing, specific to the platform we're actually on."""
    if sys.platform == "darwin":
        return "osascript not found -- this needs a standard macOS install."
    if sys.platform.startswith("linux"):
        import os

        if os.environ.get("WAYLAND_DISPLAY"):
            return "Wayland session detected but wl-clipboard is missing. Install it: sudo apt install wl-clipboard"
        if os.environ.get("DISPLAY"):
            return "X11 session detected but xclip is missing. Install it: sudo apt install xclip"
        return (
            "No graphical session detected (neither WAYLAND_DISPLAY nor DISPLAY is set). "
            "A clipboard needs a desktop session -- this will not work over a bare SSH shell."
        )
    return f"Unsupported platform: {sys.platform}"


__all__ = ["Clipboard", "BackendError", "NoBackendError", "detect"]
