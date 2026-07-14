# lazybooks

Lazy terminal access to a cloud-hosted Calibre library.

`lazybooks` is a small set of scripts for browsing a generated book manifest, fetching a selected PDF from OneDrive with `rclone`, and opening it locally. It is designed for machines where you can access OneDrive through an API/browser flow, but cannot or do not want to sync the full library into Finder.

The core workflow is:

1. Generate `index.html` and `manifest.json` somewhere in OneDrive.
2. Use `rclone` to refresh the small local manifest cache.
3. Browse/search locally.
4. Fetch one selected PDF on demand.

## Commands

- `bookrefresh`: copies `index.html` and `manifest.json` from OneDrive into a local cache.
- `bookfind`: searches the manifest from the command line and fetches one selected PDF.
- `bookpick`: uses `fzf` as a fast picker and fetches one selected PDF.
- `booktui`: full terminal UI with categories, search, cache state, and PDF fetch/open.

## Dependencies

Required:

- Python 3
- `rclone`
- A configured `rclone` remote for OneDrive

Optional:

- `fzf` for `bookpick`

On macOS with Homebrew:

```sh
brew install rclone fzf
```

## rclone setup

Create a OneDrive remote:

```sh
rclone config
```

Typical choices for a personal OneDrive:

```text
n) New remote
name> onedrive
Storage> onedrive
client_id>
client_secret>
region> global
tenant>
Edit advanced config? n
Use web browser to automatically authenticate rclone? y
```

Leave `client_id`, `client_secret`, and `tenant` blank unless you have a specific organisational setup that requires them.

Smoke test:

```sh
rclone lsf onedrive:
rclone lsf onedrive:"Library/book-indexes/assurance"
```

## Install

Clone the repo and add `bin` to your `PATH`:

```sh
git clone https://github.com/YOUR-USER/lazybooks.git
cd lazybooks
export PATH="$PWD/bin:$PATH"
```

For persistent shell setup, add this to your shell profile:

```sh
export PATH="$HOME/dev/lazybooks/bin:$PATH"
```

Or copy/symlink scripts into `~/bin`.

## Configuration

The scripts work with these defaults:

```sh
LAZYBOOKS_INDEX_REMOTE='onedrive:Library/book-indexes/assurance'
LAZYBOOKS_INDEX_DIR="$HOME/book-indexes/assurance"
LAZYBOOKS_MANIFEST="$HOME/book-indexes/assurance/manifest.json"
LAZYBOOKS_CACHE="$HOME/book-cache"
LAZYBOOKS_REMOTE='onedrive:'
LAZYBOOKS_LOCAL_PREFIX="$HOME/OneDrive/"
```

Override them in your shell profile if needed:

```sh
export LAZYBOOKS_INDEX_REMOTE='onedrive:Library/book-indexes/assurance'
export LAZYBOOKS_LOCAL_PREFIX='/path/to/local/OneDrive/'
```

`LAZYBOOKS_LOCAL_PREFIX` is important. It is the local path prefix stored in `manifest.json`; `lazybooks` rewrites that prefix to the `rclone` remote name when fetching files.

For example:

```text
/path/to/local/OneDrive/Library/assurance/...
```

becomes:

```text
onedrive:Library/assurance/...
```

## Refresh the local manifest

```sh
bookrefresh
```

This copies only:

- `index.html`
- `manifest.json`

It does not copy PDFs.

## Search from the CLI

List matches:

```sh
bookfind secure
bookfind architecture metrics
```

Fetch and open a result:

```sh
bookfind secure -n 1
```

Fetch without opening:

```sh
bookfind secure -n 1 --no-open
```

## Pick with fzf

```sh
bookpick
```

Type to filter, press Enter to fetch and open the selected book.

## Browse with the TUI

```sh
booktui
```

Keys:

- `Up` / `Down` or `k` / `j`: move
- `Tab`: switch between categories and books
- `/`: search
- `c`: clear search
- `Enter`: fetch and open selected book
- `r`: refresh manifest
- `q` or `Esc`: quit

PDFs are fetched into:

```text
~/book-cache
```

## Manifest format

`lazybooks` expects a JSON file with this shape:

```json
{
  "generated_at": "2026-07-14T12:00:00+00:00",
  "books": [
    {
      "title": "Secure by Design",
      "author": "Dan Bergh Johnsson, Daniel Deogun, Daniel Sawano",
      "category": "security-reliability",
      "canonical_path": "/path/to/local/OneDrive/Library/assurance/assurance-library-calibre/.../Secure by Design.pdf",
      "source": "Assurance Calibre"
    }
  ]
}
```

Additional fields are ignored.

## Safety notes

`lazybooks` is intentionally read-oriented:

- It does not modify Calibre metadata.
- It does not write to OneDrive except through `rclone copy` in `bookrefresh`, which copies from OneDrive to local.
- It fetches selected PDFs into a local cache.
- It avoids using a remote mount for Calibre's `metadata.db`.

This avoids the common failure mode of editing a SQLite-backed Calibre library over a cloud or API-backed filesystem.
