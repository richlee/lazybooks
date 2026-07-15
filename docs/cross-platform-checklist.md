# Cross-Platform Test Checklist

Use this checklist when testing lazybooks on a new macOS, Linux, or Windows
machine.

## Environment

- Python 3.11 or newer is installed.
- `rclone version` works.
- `rclone listremotes` shows the expected remote.
- The repository installs cleanly:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Tests

```sh
.venv/bin/python -m pytest
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\python -m pytest
```

## Config

- `~/.config/lazybooks/config.toml` or the platform equivalent exists.
- `remote` matches an `rclone` remote including the trailing colon.
- `index_remote` paths exist for each configured library.
- `local_prefix` matches the path prefix stored in `manifest.json`.
- `cache` points to a normal writable local directory.

## Refresh

```sh
bookrefresh --all
```

Expected:

- configured index files download
- PDFs are not downloaded
- missing library index folders produce clear errors

## TUI

```sh
lazybooks
```

Check:

- Tab switches only between Categories and Books.
- `/` focuses Search; `c` clears it.
- Changing category selects the first visible book.
- Books and Categories use matching gray/orange selection styling.
- `Enter` downloads/opens the selected book.
- Cached books show a green `C`.
- `d` removes only the local cached copy and only works from Books.
- `Right` or `l` opens Book Details only from Books.

## Platform-Specific

Check file opening:

- macOS: `open`
- Linux: `xdg-open`
- Windows: `os.startfile`

Check terminal behaviour:

- Unicode and colour rendering are acceptable.
- Mouse click selection behaves as expected.
- Preview/PDF viewer focus returning to the terminal is understandable.
