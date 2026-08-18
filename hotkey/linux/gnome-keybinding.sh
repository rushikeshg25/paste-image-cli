#!/usr/bin/env bash
# Register Super+Shift+V as a GNOME custom keybinding for pasteimg.
# Usage: ./gnome-keybinding.sh [binding]   e.g. ./gnome-keybinding.sh '<Super><Shift>v'
set -euo pipefail

BINDING="${1:-<Super><Shift>v}"
CMD="${HOME}/.local/bin/pasteimg"
NAME="pasteimg"
ROOT="org.gnome.settings-daemon.plugins.media-keys"
KEYPATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"

command -v gsettings >/dev/null || { echo "gsettings not found -- this script is GNOME-only." >&2; exit 1; }
[ -x "$CMD" ] || { echo "pasteimg not found at $CMD -- run install.sh first." >&2; exit 1; }

existing=$(gsettings get "$ROOT" custom-keybindings)
slot="${KEYPATH}/${NAME}/"

# Append our slot to the list unless it is already registered.
if [[ "$existing" == *"$slot"* ]]; then
  echo "Slot already registered, updating it in place."
else
  if [[ "$existing" == "@as []" || "$existing" == "[]" ]]; then
    new="['$slot']"
  else
    new="${existing%]}, '$slot']"
  fi
  gsettings set "$ROOT" custom-keybindings "$new"
fi

gsettings set "${ROOT}.custom-keybinding:${slot}" name "$NAME"
gsettings set "${ROOT}.custom-keybinding:${slot}" command "$CMD"
gsettings set "${ROOT}.custom-keybinding:${slot}" binding "$BINDING"

echo "Bound $BINDING -> $CMD"
echo "Press it with an image on the clipboard, then paste the path with Ctrl+Shift+V."
