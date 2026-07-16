# lazybooks Demo Data

This folder contains a tiny non-private demo configuration and manifest set.
It lets people open the TUI, switch libraries, browse categories, search, and
see cache markers without connecting to OneDrive or Calibre.

Run from the repository root:

```sh
lazybooks --config examples/demo/config.toml
```

The files in `examples/demo/cache/` are placeholders used only to show green
`C` cache markers in the UI. They are not real PDFs.

Opening uncached demo books will try to use the fake `demo:` rclone remote and
is expected to fail. The demo is intended for browsing and screenshots.
