# herdr config

`create_symlink.sh` links `config.toml` to `~/.config/herdr/config.toml`.

## How the file is built

It is `herdr --default-config` output (currently herdr 0.7.4) used verbatim as the
base, with our own values written on top of it as active lines. Two consequences:

- Every option herdr supports is documented right here, and each one's stock default
  is visible on the commented line above ours.
- `diff <(herdr --default-config) config.toml` is the complete list of what we changed.

## Editing rules

- Put each of our values **directly under** the commented default line it overrides.
  Never place it somewhere else; the link to the default it replaces is what makes
  the file readable.
- Leave options delegated to herdr's default commented out. Do not delete them.
- **Do not write comments explaining how or why a value deviates from the default.**
  The value sits right under its default, so the deviation is already visible line by
  line, and the diff above enumerates all of it.
- **Do write a comment for entries the default config has no equivalent for.**
  A `[[keys.command]]` shell or plugin binding, or a custom sidebar row fed by
  externally pushed metadata, gives no clue about what it does from its command
  string alone.
- Keep `[ui]` scalar keys **before** any table header such as `[ui.sidebar.spaces]`.
  Once a header is active, every key that follows belongs to that table.
- After editing, confirm the file still parses as TOML:
  `python3 -c "import tomllib;tomllib.load(open('config.toml','rb'))"`

## On a herdr upgrade

Diff the new `herdr --default-config` output against this file and fold in the
options that were added upstream. The version this file was built from is recorded
in the header comment.
