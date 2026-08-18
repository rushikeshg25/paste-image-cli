#!/usr/bin/env bash
# Symlink pasteimg into ~/.local/bin and print the hotkey setup for this OS.
# Touches nothing else -- no shell rc files, no system config.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
TARGET="${BIN_DIR}/pasteimg"

command -v python3 >/dev/null || { echo "python3 is required but not found." >&2; exit 1; }

mkdir -p "$BIN_DIR"
ln -sf "${REPO}/pasteimg" "$TARGET"
echo "Linked $TARGET -> ${REPO}/pasteimg"

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *) echo "NOTE: ${BIN_DIR} is not on your PATH. Add it to your shell rc." ;;
esac

echo
case "$(uname -s)" in
  Darwin)
    if [ ! -d /Applications/Hammerspoon.app ]; then
      echo "Hotkey setup (macOS):"
      echo "  1. brew install --cask hammerspoon"
      echo "  2. mkdir -p ~/.hammerspoon && ln -s ${REPO}/hotkey/macos/init.lua ~/.hammerspoon/init.lua"
      echo "  3. Launch Hammerspoon and grant Accessibility permission."
    else
      echo "Hammerspoon found. Link the config:"
      echo "  ln -s ${REPO}/hotkey/macos/init.lua ~/.hammerspoon/init.lua"
      echo "  (already have an init.lua? add: dofile(\"${REPO}/hotkey/macos/init.lua\"))"
    fi
    echo "Then: Cmd+Shift+V grabs the image, Cmd+V pastes the path."
    ;;
  Linux)
    missing=""
    if [ -n "${WAYLAND_DISPLAY:-}" ]; then
      command -v wl-paste >/dev/null || missing="wl-clipboard"
    else
      command -v xclip >/dev/null || missing="xclip"
    fi
    [ -n "$missing" ] && echo "Install the clipboard tool first: sudo apt install $missing" && echo
    echo "Hotkey setup (Linux):"
    echo "  GNOME:  ${REPO}/hotkey/linux/gnome-keybinding.sh"
    echo "  i3/bspwm/Hyprland: see ${REPO}/hotkey/linux/sxhkdrc.example"
    echo "Then: Super+Shift+V grabs the image, Ctrl+Shift+V pastes the path."
    ;;
esac
