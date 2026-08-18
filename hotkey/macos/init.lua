-- pasteimg -- Hammerspoon binding.
--
-- Cmd+Shift+V: pull the clipboard image to a file and put its path on the
-- clipboard. Then press Cmd+V in any CLI agent to paste the path.
--
-- Install:
--   brew install --cask hammerspoon
--   mkdir -p ~/.hammerspoon
--   ln -s <repo>/hotkey/macos/init.lua ~/.hammerspoon/init.lua
-- (or `dofile("<repo>/hotkey/macos/init.lua")` from an existing init.lua)
--
-- Hammerspoon needs Accessibility permission, granted once on first launch.

local PASTEIMG = os.getenv("HOME") .. "/.local/bin/pasteimg"
local HOTKEY = { { "cmd", "shift" }, "v" }

-- Auto-paste after grabbing. Set false to just load the clipboard and paste
-- yourself. Requires Accessibility permission to synthesise the keystroke.
local AUTO_PASTE = false

local function grab()
  -- hs.task is async, so Hammerspoon never blocks on osascript.
  local task = hs.task.new(PASTEIMG, function(exitCode, stdout, stderr)
    if exitCode == 0 then
      local path = (stdout or ""):gsub("%s+$", "")
      local name = path:match("([^/]+)$") or path
      hs.alert.show(name, 0.8)
      if AUTO_PASTE then
        hs.eventtap.keyStroke({ "cmd" }, "v", 0)
      end
    elseif exitCode == 1 then
      hs.alert.show("No image on clipboard", 1.2)
    else
      hs.alert.show("pasteimg: " .. ((stderr or "failed"):gsub("%s+$", "")), 2.5)
    end
  end, { "--no-notify" })

  if not task then
    hs.alert.show("pasteimg not found at " .. PASTEIMG, 3)
    return
  end
  task:start()
end

hs.hotkey.bind(HOTKEY[1], HOTKEY[2], grab)
hs.alert.show("pasteimg ready (⌘⇧V)", 1)
