-- Hammerspoon entry point.
--
-- Keep this file thin: every feature lives in its own module under
-- ~/.hammerspoon/ and is required from here, so new automations can be
-- added side by side without touching existing ones.

-- Toggle Chrome's native vertical tab sidebar (Cmd+S / left-edge hover).
-- Vendored from an upstream project; see README.md for details.
require("chrome-vertical-tab-sidebar-toggle")
