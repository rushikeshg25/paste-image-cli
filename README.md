# paste-image-cli

Paste clipboard images into terminal-based coding agents such as Codex and
Claude Code.

Terminal applications receive text from the terminal, not image bytes from the
desktop clipboard. `pasteimg` bridges that gap: it saves the clipboard image to
a local file, copies the file path as text, and lets you paste that path into
the agent.

```text
desktop clipboard image
        │
        ▼
     pasteimg ──► ~/.cache/paste-cli-agent/clip-….png
        │
        ▼
clipboard now contains the local path ──► paste into Codex or Claude Code
```

It runs on macOS, Linux/Wayland, and Linux/X11. The CLI uses only the Python
standard library.

## Quick start

### Ubuntu or Debian on Wayland

```bash
sudo apt install wl-clipboard
git clone https://github.com/rushikeshg25/paste-image-cli.git
cd paste-image-cli
./install.sh
./hotkey/linux/gnome-keybinding.sh   # GNOME only
```

Copy a screenshot or image, press `Super+Shift+V`, then press
`Ctrl+Shift+V` in the terminal to paste its saved path.

### Linux on X11

```bash
sudo apt install xclip
git clone https://github.com/rushikeshg25/paste-image-cli.git
cd paste-image-cli
./install.sh
```

GNOME users can run `./hotkey/linux/gnome-keybinding.sh`. i3, bspwm, and
Hyprland users can copy the relevant binding from
[`hotkey/linux/sxhkdrc.example`](hotkey/linux/sxhkdrc.example).

### macOS

```bash
git clone https://github.com/rushikeshg25/paste-image-cli.git
cd paste-image-cli
./install.sh
brew install --cask hammerspoon
mkdir -p ~/.hammerspoon
ln -s "$PWD/hotkey/macos/init.lua" ~/.hammerspoon/init.lua
```

Launch Hammerspoon, grant Accessibility permission when prompted, copy an
image, press `Cmd+Shift+V`, then press `Cmd+V` in the terminal.

If you already have `~/.hammerspoon/init.lua`, add this instead of replacing
the file:

```lua
dofile("/absolute/path/to/paste-image-cli/hotkey/macos/init.lua")
```

## Requirements

| Platform | Required software | Clipboard backend |
| --- | --- | --- |
| macOS | Python 3.9+, `osascript`, and `sips` | Native AppleScript tools |
| Linux/Wayland | Python 3.9+ and `wl-clipboard` | `wl-paste` / `wl-copy` |
| Linux/X11 | Python 3.9+ and `xclip` | `xclip` |

`osascript` and `sips` are included with macOS. There are no pip packages, no
virtual environment, and no compiled components.

To check which Linux session you are using:

```bash
echo "$XDG_SESSION_TYPE"
```

## Installation details

`./install.sh` creates this symlink:

```text
~/.local/bin/pasteimg -> /absolute/path/to/the/checkout/pasteimg
```

The checkout must remain at that location. The installer does not copy project
files, edit shell startup files, install packages, or use `sudo`. If
`~/.local/bin` is not on `PATH`, it prints a note; you can still run the
executable directly as `./pasteimg`.

Confirm the installation with:

```bash
pasteimg --version
pasteimg --help
```

## Everyday workflow

1. Copy an image, a screenshot, or an image file in Finder/Nautilus.
2. Run `pasteimg`, either from the command line or with the configured hotkey.
3. `pasteimg` saves the image and replaces the clipboard contents with its path.
4. Paste the path into the terminal agent.

The CLI also prints the path, making it useful in scripts:

```console
$ pasteimg
/home/alice/.cache/paste-cli-agent/clip-20260819-144745.png
```

When you copy an existing image file from Finder or Nautilus, `pasteimg` reuses
that file's path instead of duplicating it in the cache.

## Commands

| Command | Behavior |
| --- | --- |
| `pasteimg` | Save the image, copy its path, show a notification, and print the path. |
| `pasteimg --print` | Save and print the path without replacing the clipboard. |
| `pasteimg --json` | Save the image and print structured metadata; the clipboard is unchanged. |
| `pasteimg --last` | Print the most recently cached image path without reading or changing the clipboard. |
| `pasteimg --codex` | Save the image, then replace the process with `codex -i <path>`. |
| `pasteimg --no-notify` | Perform the normal clipboard flow without a desktop notification. |
| `pasteimg --prune-days N` | Set cache retention for this run; `0` disables pruning. |
| `pasteimg --version` | Print the installed version. |

### Script-friendly JSON

```console
$ pasteimg --json
{"path": "/home/alice/.cache/paste-cli-agent/clip-20260819-144745.png", "bytes": 5278, "backend": "wayland", "reused": false}
```

Fields:

| Field | Meaning |
| --- | --- |
| `path` | Absolute path that the agent can read. |
| `bytes` | Size of the saved or reused file. |
| `backend` | `macos`, `wayland`, `x11`, or `cache` for `--last`. |
| `reused` | `true` when no new cached copy was needed. |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | No supported image is on the clipboard |
| `2` | A platform clipboard command failed |
| `3` | No usable clipboard backend was detected |

## Hotkeys

The hotkey layer is optional; it only launches `~/.local/bin/pasteimg`.

| Desktop | Setup | Default binding |
| --- | --- | --- |
| macOS/Hammerspoon | Link or load `hotkey/macos/init.lua` | `Cmd+Shift+V` |
| GNOME | Run `hotkey/linux/gnome-keybinding.sh` | `Super+Shift+V` |
| i3 | Use the example config | `Mod+Shift+V` |
| bspwm/sxhkd | Use the example config | `Super+Shift+V` |
| Hyprland | Use the example config | `Super+Shift+V` |

Pass a different GNOME binding as the first argument if the default conflicts
with another shortcut:

```bash
./hotkey/linux/gnome-keybinding.sh '<Super><Alt>v'
```

The Hammerspoon config contains an `AUTO_PASTE` setting. Its default is `false`
because automatic paste sends a keystroke to whichever application currently
has focus. Set it to `true` if you want one-key image insertion on macOS.

Because the shortcut is registered with the operating system, it works
independently of the terminal emulator. This is useful for terminals that cannot
bind a key directly to an external command.

## Image formats

On Wayland and X11, the backend prefers clipboard data in this order:

1. PNG
2. JPEG
3. GIF
4. WebP
5. TIFF

On macOS, it reads PNG, JPEG, GIF, and TIFF clipboard data. macOS screenshots
commonly use TIFF internally, so `pasteimg` converts them to PNG with `sips`
when possible.

Existing image file references with these extensions can be reused directly:
`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.tiff`, `.tif`, `.bmp`, and `.heic`.

## Cache, retention, and privacy

New images are stored under:

```text
$XDG_CACHE_HOME/paste-cli-agent
```

If `XDG_CACHE_HOME` is unset, the location is:

```text
~/.cache/paste-cli-agent
```

Files use timestamped names such as `clip-20260819-144745.png`. Name collisions
within the same second get a numeric suffix and never overwrite an earlier
image.

The default retention period is seven days. Pruning runs after a new clipboard
image is saved and only removes files whose names begin with `clip-` inside the
tool's own cache directory. Reused source files are never deleted.

Everything happens locally. `pasteimg` does not upload images, call a network
service, or send telemetry. The coding agent may read the local path after you
paste it, so apply the same care you would when attaching an image normally.

## Troubleshooting

### “No image on the clipboard”

The clipboard currently exposes no supported image data. Copy the screenshot or
image itself, not text containing an image URL, then try:

```bash
pasteimg --print
```

On Wayland, inspect the advertised clipboard formats with:

```bash
wl-paste --list-types
```

On X11:

```bash
xclip -selection clipboard -t TARGETS -o
```

At least one supported image MIME type must appear.

### “No usable clipboard backend”

Check the session and required command:

```bash
echo "session=$XDG_SESSION_TYPE"
command -v wl-paste wl-copy   # Wayland
command -v xclip              # X11
```

Install `wl-clipboard` or `xclip` as appropriate. A bare SSH session normally
has no access to the desktop clipboard; run `pasteimg` inside the graphical
desktop session.

### The GNOME shortcut does nothing

First run `pasteimg` manually. If that succeeds, confirm the executable and
re-register the binding:

```bash
ls -l ~/.local/bin/pasteimg
./hotkey/linux/gnome-keybinding.sh
```

Also check GNOME Settings for another action using `Super+Shift+V`. You can
choose a different key combination with the script argument shown above.

### The path appears, but does not paste into the terminal

Use the terminal's text-paste shortcut after running `pasteimg`:

- Linux terminals commonly use `Ctrl+Shift+V`.
- macOS terminals commonly use `Cmd+V`.
- Some editors or embedded terminals override these defaults.

You can verify the current clipboard text directly:

```bash
wl-paste --no-newline             # Wayland
xclip -selection clipboard -o    # X11
pbpaste                           # macOS
```

### Notifications are unavailable

Notifications are best-effort and never make a successful image capture fail.
Linux uses `notify-send`; install your distribution's `libnotify` tools if you
want notifications, or use `--no-notify`.

## Uninstalling

Remove the executable symlink:

```bash
rm ~/.local/bin/pasteimg
```

Then remove the custom shortcut from GNOME Settings or the relevant line from
your window-manager configuration. On macOS, remove the Hammerspoon symlink or
the `dofile(...)` line and reload Hammerspoon. The checkout and cached images
remain yours to inspect or remove separately.

## Architecture

Platform behavior is isolated behind the `Clipboard` interface in
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

`core.py` implements the common grab/save/report flow. `backends.detect()`
selects a platform implementation and prefers Wayland over X11 when both
display variables exist, avoiding accidental routing through XWayland.

| Module | Responsibility |
| --- | --- |
| `pasteimg` | Executable entry point that also works from a checkout |
| `pasteimg_lib/cli.py` | Arguments, output modes, and exit codes |
| `pasteimg_lib/core.py` | Platform-independent clipboard-to-file flow |
| `pasteimg_lib/store.py` | Cache paths, collision handling, and retention |
| `pasteimg_lib/backends/macos.py` | AppleScript and `sips` integration |
| `pasteimg_lib/backends/wayland.py` | `wl-clipboard` integration |
| `pasteimg_lib/backends/x11.py` | `xclip` integration |
| `hotkey/` | Optional OS and desktop shortcut configurations |

## Development and tests

Run the complete suite with the system Python:

```bash
python3 -m unittest discover -s tests -t .
```

The tests use only `unittest`. The core flow is exercised through an in-memory
clipboard implementation, so most behavior is testable without changing the
real clipboard. Backend tests cover platform-specific parsing and process
behavior. GitHub Actions runs the compile check, CLI smoke test, and full suite
on Ubuntu and macOS with Python 3.9 and Python 3.14.

Current platform status:

| Platform | Status |
| --- | --- |
| macOS | Verified end to end with PNG, TIFF conversion, file reuse, and empty-clipboard handling |
| Ubuntu GNOME/Wayland | Verified end to end with real `wl-paste` / `wl-copy` image and text transfers |
| Linux/X11 | Implemented and covered by the shared tests; hardware verification is still welcome |

To add another platform, implement `Clipboard` in a new backend module and add
the class to `_PROBE` in `pasteimg_lib/backends/__init__.py`. The core flow does
not need to change.

## License

[MIT](LICENSE)
