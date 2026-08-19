# Hammerspoon

[Hammerspoon](https://www.hammerspoon.org/) configuration.

`init.lua` is a thin entry point: it only `require`s the feature modules that sit
next to it, so new automations can be added without touching existing ones.
`create_symlink.sh` symlinks both `init.lua` and every module into `~/.hammerspoon/`,
which is on Hammerspoon's `package.path`.

Modules:

| File | What it does |
| --- | --- |
| `chrome-vertical-tab-sidebar-toggle.lua` | Toggles Chrome's native vertical tab sidebar with `Cmd+S` and a left-edge mouse hover |

## Vendoring

`chrome-vertical-tab-sidebar-toggle.lua` is vendored from
[Ha1baraA11/Chrome-Vertical-Tab-Sidebar-Toggle](https://github.com/Ha1baraA11/Chrome-Vertical-Tab-Sidebar-Toggle)
at commit `c4c1bf080867d16d9e5888857afbbd93eb53af7a` (its `init.lua`).
It is MIT licensed; the upstream license text is kept as
`LICENSE.chrome-vertical-tab-sidebar-toggle`.

The only local change is `DEBUG = false`, so that the Hammerspoon Console does not
fill up while Chrome is in use. Everything else is upstream as-is, including
`SCHEME = 3` (keyboard + mouse), the `Cmd+S` binding, and the edge thresholds.

To see the current diff against upstream `main`:

```sh
curl -fsSL https://raw.githubusercontent.com/Ha1baraA11/Chrome-Vertical-Tab-Sidebar-Toggle/main/init.lua \
  | diff - chrome-vertical-tab-sidebar-toggle.lua
```

Pin any re-import to a reviewed commit rather than tracking `main`: Hammerspoon runs
with Accessibility permission, so this code can observe every keystroke and drive the
UI of every app. Read the diff before taking an update.

## Manual setup

Steps 3 to 6 cannot be automated and have to be done once per machine.

1. Install Hammerspoon — the `homebrew-cask` role of `dotfiles-ansible` does this
   (`brew install --cask hammerspoon` by hand also works).
2. Run `create_symlink.sh` to populate `~/.hammerspoon/`.
3. Grant Accessibility permission: System Settings → Privacy & Security →
   Accessibility → enable Hammerspoon. The TCC database is protected by SIP, so this
   cannot be scripted.
4. Enable the sidebar in Chrome: open `chrome://flags/#vertical-tabs`, set it to
   Enabled, and restart Chrome.
5. In Hammerspoon Preferences, enable "Launch Hammerspoon at login" (and turn off
   "Show menu icon" if it is in the way).
6. Hammerspoon menu → Reload Config.

## Usage

| Trigger | Effect |
| --- | --- |
| `Cmd+S` (Chrome frontmost only) | Toggle the sidebar |
| Move the pointer to the left screen edge (0-2px) | Expand the sidebar |
| Move the pointer past 380px from the left edge | Collapse the sidebar |
| `Cmd+Alt+D` | Show service status |
| `Cmd+Alt+B` | Dump Chrome's AX buttons to the Console |
| `Cmd+Alt+R` | Restart the services |

## Caveats

- `Cmd+S` shadows Chrome's "Save page as" while Hammerspoon is running: the key is
  swallowed whenever Chrome is frontmost. To use a different shortcut, edit the
  modifier flags and `keycodes.map["s"]` inside `createKeyTap`.
- The three debug hotkeys are registered globally, not just for Chrome, so they can
  collide with other apps.
- The sidebar button is located by its accessibility label, so detection depends on
  Chrome's UI language. `SIDEBAR_LABELS` covers English, Japanese, and several others;
  add an entry for any other language you switch Chrome to.
- If the sidebar stops responding after switching apps or waking from sleep, a
  Hammerspoon watcher may have been garbage collected — upstream does not keep a
  reference to the objects returned by `appWatcher.new(...)` and
  `caffeinate.watcher.new(...)`. Try `Cmd+Alt+R` first; if it keeps happening,
  consider holding those watchers in module-level variables.
