"""pasteimg -- put a clipboard image on disk so CLI agents can read it.

A terminal only forwards text over the TTY, so clipboard image bytes never
reach a TUI process. This turns the image into a file path, which is text.
"""

__version__ = "0.1.0"
