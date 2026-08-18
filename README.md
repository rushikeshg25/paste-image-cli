# paste-image-cli

Paste clipboard images into terminal-based coding agents such as Claude Code and
Codex. Runs on macOS and Linux.

## The problem

A terminal emulator forwards only *text* over the TTY. Image data on the system
clipboard therefore never reaches a process running inside the terminal, and no
amount of support on the agent's side changes that — the bytes are not delivered
to it in the first place.

`pasteimg` closes the gap by writing the clipboard image to disk and putting its
**path** on the clipboard instead. A path is text, so it survives the TTY, and
both agents read images from disk:

    Cmd+Shift+V   image saved to ~/.cache/paste-cli-agent/clip-20260818-201235.png
                  path to that file copied to the clipboard
    Cmd+V         path pasted into the agent, which reads the image from disk

## Requirements

- Python 3.9 or newer (standard library only — no pip packages, no virtualenv)
- macOS: nothing further; `osascript` and `sips` ship with the system
- Linux: `wl-clipboard` on Wayland, or `xclip` on X11

## Installation

    git clone https://github.com/rushikeshg25/paste-image-cli.git
    cd paste-image-cli
    ./install.sh

The installer symlinks `pasteimg` into `~/.local/bin` and prints the hotkey setup
for the detected platform. It modifies nothing else — no shell rc files, no
system configuration.

On Linux, install the clipboard tool first if it is missing:

    sudo apt install wl-clipboard    # Wayland
    sudo apt install xclip           # X11

## Hotkey setup

The hotkey is optional. It is a thin wrapper around the CLI, so `pasteimg` works
standalone if you would rather not run a hotkey daemon.

| Platform | Setup | Default binding |
| --- | --- | --- |
| macOS | `brew install --cask hammerspoon`, then link `hotkey/macos/init.lua` to `~/.hammerspoon/init.lua` | `Cmd+Shift+V` |
| GNOME | `hotkey/linux/gnome-keybinding.sh` | `Super+Shift+V` |
| i3, bspwm, Hyprland | see `hotkey/linux/sxhkdrc.example` | `Super+Shift+V` |

Hammerspoon is the only third-party dependency in the project, and it is confined
to the macOS hotkey layer; `pasteimg` itself never references it. Hammerspoon
requires Accessibility permission, granted once on first launch.

`init.lua` exposes an `AUTO_PASTE` flag that synthesises the paste keystroke for
you. It is disabled by default, because it sends a keystroke to whichever
application currently has focus.

Because the hotkey operates on the OS clipboard rather than through the terminal,
it behaves identically in Ghostty, iTerm2, Terminal.app, and VS Code. Note that
Ghostty has no keybind action for running a shell command, so an OS-level hotkey
is the only option there regardless.

## Usage

| Command | Behaviour |
| --- | --- |
| `pasteimg` | Save the image, copy its path to the clipboard, notify, print the path. This is what the hotkey invokes. |
| `pasteimg --print` | Save and print the path; leave the clipboard untouched. |
| `pasteimg --json` | Emit `{"path":…,"bytes":…,"backend":…,"reused":…}` for scripting. |
| `pasteimg --last` | Print the most recently saved path without reading the clipboard. |
| `pasteimg --codex` | Save, then hand the image to `codex -i <path>`. |
| `pasteimg --prune-days N` | Override retention (default 7 days; `0` disables pruning). |
| `pasteimg --no-notify` | Suppress the desktop notification. |

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | No image on the clipboard |
| 2 | A platform command failed |
| 3 | No usable clipboard backend |

### Behaviour notes

When the clipboard holds an image *file* copied from Finder or Nautilus, that
path is reused directly rather than duplicated into the cache. Such results are
reported with `"reused": true`.

Saved images are written to `$XDG_CACHE_HOME/paste-cli-agent`, falling back to
`~/.cache/paste-cli-agent`, and are pruned after seven days. Pruning only ever
removes files this tool created, identified by filename prefix within its own
cache directory.

macOS screenshots are placed on the clipboard as TIFF. These are converted to PNG
via `sips` on extraction, so the agent always receives a widely supported format.

## Architecture

All platform-specific behaviour sits behind a single interface, `Clipboard`, in
`pasteimg_lib/backends/base.py`:

```python
class Clipboard(ABC):
    @classmethod
    def available(cls) -> bool: ...
    def read_image(self) -> tuple[bytes, str] | None: ...
    def read_file_urls(self) -> list[str]: ...
    def write_text(self, text: str) -> None: ...
    def notify(self, title: str, body: str) -> None: ...
```

`core.py` implements the grab-save-report flow once, against that interface, and
contains no OS-specific code.

| Backend | Platform | Underlying tools |
| --- | --- | --- |
| `macos.py` | macOS | `osascript`, `sips` |
| `wayland.py` | Linux, Wayland | `wl-paste`, `wl-copy` |
| `x11.py` | Linux, X11 | `xclip` |

`backends.detect()` probes these in order, preferring Wayland over X11 so that a
session running XWayland is not misrouted through `xclip`. Supporting an
additional platform requires one new module and one entry in `_PROBE`; `core.py`
is unaffected.

The macOS backend extracts images by having AppleScript coerce the clipboard to a
target type and write the raw bytes straight to a file, avoiding a hex round-trip
through the shell.

### Project layout

    pasteimg                    executable entrypoint
    pasteimg_lib/
      cli.py                    argument parsing, output modes, exit codes
      core.py                   platform-agnostic flow: grab, save, report
      store.py                  cache directory, filenames, retention
      backends/base.py          the Clipboard interface
      backends/macos.py         macOS implementation
      backends/wayland.py       Wayland implementation
      backends/x11.py           X11 implementation
    hotkey/                     per-platform key bindings
    install.sh                  symlink and setup instructions
    tests/

## Tests

    python3 -m unittest discover -s tests -t .

Written against the standard library's `unittest`; there are no test
dependencies. `tests/test_backends_fake.py` drives the complete core flow against
an in-memory `Clipboard` implementation, so the full path — including file reuse
and fallback behaviour — is exercised on any OS without touching a real
clipboard.

## Platform status

The macOS backend is verified end to end against real clipboard data: PNG
extraction is byte-identical to the source, TIFF is converted correctly, file
reuse avoids duplication, and the no-image case exits cleanly.

The Wayland and X11 backends are implemented but **have not yet been tested on
hardware**. The core flow they plug into is covered by the test suite, but the
`wl-paste` and `xclip` invocations themselves need verification on a Linux
desktop session.

## Licence

MIT
