# lazybooks

[![Tests](https://github.com/richlee/lazybooks/actions/workflows/tests.yml/badge.svg)](https://github.com/richlee/lazybooks/actions/workflows/tests.yml)

Lazy terminal access to cloud-hosted book libraries.

`lazybooks` is a small set of command-line tools for browsing generated book
manifests, fetching a selected PDF from an `rclone` remote, and opening it
locally. It is useful on machines where you can authenticate to OneDrive through
`rclone`, but cannot or do not want to sync the whole library into Finder.

The normal workflow is:

1. Keep the source libraries in OneDrive, optionally managed by Calibre.
2. Generate a small `index.html` and `manifest.json` for each library.
3. Upload those index files to OneDrive.
4. Refresh the local manifest cache on any machine.
5. Browse locally and fetch individual PDFs on demand.

## Commands

- `lazybooks`: full terminal UI with categories, search, cache state, PDF fetch/open, and cached-copy delete.
- `lazybooks-curses`: legacy fallback for the original curses TUI.
- `bookrefresh`: copies `index.html` and `manifest.json` from OneDrive into a local cache.
- `bookfind`: searches a manifest from the command line and fetches one selected PDF.
- `bookpick`: uses `fzf` as a fast picker and fetches one selected PDF.
- `bookindex`: builds `index.html` and `manifest.json` for a folder of PDFs.
- `booktaxonomy`: proposes and optionally applies cleaner Calibre taxonomy tags.

## Dependencies

Required:

- Python 3.11 or newer
- `rclone`
- A configured `rclone` remote for your cloud storage
- Textual, installed through the Python package metadata

Optional:

- `fzf` for `bookpick`
- Calibre, if you want Calibre-managed metadata and tags

On macOS with Homebrew:

```sh
brew install rclone fzf
```

## Install For Use

Clone the repo and install the package in a virtual environment:

```sh
git clone https://github.com/richlee/lazybooks.git
cd lazybooks
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

The package install provides the main commands:

```sh
lazybooks --version
bookrefresh --help
bookfind --help
```

Some helper scripts are still distributed from `bin/`. For `bookindex`,
`bookpick`, `booktaxonomy`, and `lazybooks-curses`, add `bin` to your `PATH`:

```sh
export PATH="$PWD/bin:$PATH"
```

For persistent shell setup, add the path to your shell profile:

```sh
export PATH="$HOME/dev/lazybooks/bin:$PATH"
```

For an isolated user install from a checkout:

```sh
pipx install .
```

## rclone Setup

Create a OneDrive remote:

```sh
rclone config
```

Typical choices for a personal OneDrive:

```text
n) New remote
name> personal-onedrive
Storage> onedrive
client_id>
client_secret>
region> global
tenant>
Edit advanced config? n
Use web browser to automatically authenticate rclone? y
```

Leave `client_id`, `client_secret`, and `tenant` blank unless you have a
specific organisational setup that requires them.

Smoke test:

```sh
rclone lsf personal-onedrive:
rclone lsf personal-onedrive:"Library"
```

The examples below assume a remote named `personal-onedrive:`. If yours is named
`onedrive:`, use that instead.

## Configuration

Create `~/.config/lazybooks/config.toml`:

```toml
default = "assurance"
cache = "~/book-cache"
remote = "personal-onedrive:"
local_prefix = "~/Library/CloudStorage/OneDrive-Personal/"

[libraries.assurance]
name = "Assurance"
index_dir = "~/book-indexes/assurance"
index_remote = "personal-onedrive:Library/book-indexes/assurance"

[libraries.tech]
name = "Tech"
index_dir = "~/book-indexes/tech"
index_remote = "personal-onedrive:Library/book-indexes/tech"

[libraries.personal]
name = "Personal"
index_dir = "~/book-indexes/personal"
index_remote = "personal-onedrive:Library/book-indexes/personal"
```

Important fields:

- `default`: the library opened by `bookrefresh` or `lazybooks` when no library is specified.
- `cache`: where downloaded PDFs are stored locally.
- `remote`: the `rclone` remote used to fetch PDFs.
- `local_prefix`: the local filesystem prefix stored in generated manifests.
- `index_dir`: where each library's small local `index.html` and `manifest.json` live.
- `index_remote`: where those index files live in OneDrive.

`local_prefix` matters because manifests store local-looking paths such as:

```text
/Users/me/Library/CloudStorage/OneDrive-Personal/Library/tech/...
```

`lazybooks` rewrites that prefix to the configured remote when fetching:

```text
personal-onedrive:Library/tech/...
```

An example config is included at `examples/config.toml`.

Environment variables such as `LAZYBOOKS_REMOTE` can override some config values,
but a config file is easier for multi-library use.

## Build Indexes

`bookindex` writes two files:

- `index.html`: a simple browser-friendly index.
- `manifest.json`: the data used by `lazybooks`, `bookfind`, and `bookpick`.

For a Calibre-backed library:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/tech-library-calibre" \
  --index-dir "$HOME/book-indexes/tech" \
  --title "Tech Books" \
  --library-name Tech \
  --calibre-metadata-only
```

With `--calibre-metadata-only`, `bookindex` indexes PDFs referenced by Calibre's
`metadata.db`, and uses Calibre title, author, and first tag as the browsing
category.

For a folder of PDFs without Calibre metadata:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/reference-pdfs" \
  --index-dir "$HOME/book-indexes/reference" \
  --title "Reference Books" \
  --library-name Reference \
  --category-depth 2
```

For non-Calibre folders, categories come from folder names. `--category-depth 2`
uses the first two path components under the root.

## Publish Indexes To OneDrive

After building an index, upload only the small index files:

```sh
rclone copy "$HOME/book-indexes/tech" \
  personal-onedrive:Library/book-indexes/tech \
  --filter '+ index.html' \
  --filter '+ manifest.json' \
  --filter '- *'
```

Repeat for each library you want available from other machines.

Then verify the configured refresh path:

```sh
bookrefresh tech
bookrefresh --all
```

`bookrefresh` copies only `index.html` and `manifest.json`. It does not copy
PDFs.

## Taxonomies

The TUI categories come from each book's `category` field in `manifest.json`.
For Calibre-backed libraries, `bookindex` currently derives that category from
the first Calibre tag on the book.

Good taxonomy tags are broad enough to group related books, but specific enough
to help browsing. Prefer a small controlled list:

```text
cloud-devops-platform
software-architecture-design
programming-languages
engineering-leadership-career
buddhism-meditation
health-fitness-nutrition
philosophy-consciousness
```

Avoid tags that are too broad, too narrow, or accidental:

```text
computing
personal
self
MEAP V14
JOHN STARR...
SEL031000
Mindrolling Lotus Garden
```

### Review Proposed Taxonomies

`booktaxonomy` uses the refreshed manifests to find the configured Calibre
libraries, then looks at title, author, existing tags, and comments before
writing review files:

```sh
booktaxonomy tech personal
```

Output:

```text
reports/taxonomy-proposal.md
reports/tech-taxonomy-proposal.csv
reports/personal-taxonomy-proposal.csv
```

The CSV includes:

- current Calibre tags
- recurring tags, excluding one-off tag noise
- proposed taxonomy category
- confidence
- reason

The generated reports are local and gitignored because they can contain private
book titles.

### Improve The Taxonomy

The current classifier is deliberately simple and lives in `bin/booktaxonomy`.
The rule lists are:

- `TECH_RULES`
- `PERSONAL_RULES`

Each rule maps a category to title/tag/comment keywords. Edit those rules when a
category is too broad, too narrow, or repeatedly wrong.

This is a good place for manual or assistive AI review:

1. Run `booktaxonomy tech personal`.
2. Review `reports/*-taxonomy-proposal.csv`.
3. Look especially at `*-manual-review`, low-confidence rows, and categories with only one or two books.
4. Ask an assistant or LLM to propose a smaller controlled taxonomy from the CSV, but check the result yourself.
5. Update the rules in `bin/booktaxonomy`.
6. Rerun `booktaxonomy` until the category list is useful.

Do not aim for perfect classification. A manual-review bucket is better than
inventing misleading categories from poor metadata.

### Apply Taxonomy Tags To Calibre

When the proposal looks good:

```sh
booktaxonomy tech personal --apply
```

`--apply` creates a timestamped backup beside each Calibre database:

```text
metadata.db.lazybooks-backup-YYYYMMDD-HHMMSS
```

It then replaces each selected Calibre book's tags with its proposed taxonomy
category. It works on all Calibre book records in the selected libraries, not
just PDFs.

After applying tags, rebuild and publish the affected indexes:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/tech-library-calibre" \
  --index-dir "$HOME/book-indexes/tech" \
  --title "Tech Books" \
  --library-name Tech \
  --calibre-metadata-only

rclone copy "$HOME/book-indexes/tech" \
  personal-onedrive:Library/book-indexes/tech \
  --filter '+ index.html' \
  --filter '+ manifest.json' \
  --filter '- *'

bookrefresh tech
```

## Browse With The TUI

```sh
lazybooks
```

`lazybooks` is the Textual TUI from v0.2 onward. The original curses
implementation is available as a legacy fallback:

```sh
lazybooks-curses
```

Keys:

- Move: `Up` / `Down` or `k` / `j`
- Pane: `Tab`
- Search: `/`
- Clear search: `c`
- Open: `Enter`
- Details: `Right` or `l`
- Delete cache: `d`
- Library: `1`-`9`
- Refresh: `r`
- About: `?`
- Quit: `q` or `Esc`

PDFs are fetched into the configured cache, usually:

```text
~/book-cache
```

Deleting a cached book only removes the local downloaded copy. It does not touch
OneDrive, Calibre, or the manifest.

## Development

Install development dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Run tests:

```sh
.venv/bin/python -m pytest
```

The test suite uses temporary manifests and cache directories. It does not need
access to your OneDrive, Calibre libraries, or personal config.

Before a release, also run:

```sh
.venv/bin/python -m py_compile lazybooks/*.py lazybooks/cli/*.py lazybooks/tui/*.py
.venv/bin/lazybooks --version
```

## Public Readiness

The core v0.2 product is usable, but a more public-facing release still needs:

- screenshots or a short terminal GIF
- cross-platform smoke testing on macOS, Linux, and Windows
- confirmation of `rclone`, path, and file-opening behaviour on each platform
- a short GitHub release note for each tagged release
- a decision on whether to move remaining helper scripts into package entry points

Use `docs/cross-platform-checklist.md` for platform test passes.

## Search From The CLI

List matches:

```sh
bookfind secure
bookfind architecture metrics
bookfind --library tech kubernetes
```

Fetch and open a result:

```sh
bookfind secure -n 1
```

Fetch without opening:

```sh
bookfind secure -n 1 --no-open
```

## Pick With fzf

```sh
bookpick
bookpick tech
```

Type to filter, press Enter to fetch and open the selected book.

## Manifest Format

`lazybooks` expects a JSON file with this shape:

```json
{
  "generated_at": "2026-07-14T12:00:00+00:00",
  "books": [
    {
      "title": "Secure by Design",
      "author": "Dan Bergh Johnsson, Daniel Deogun, Daniel Sawano",
      "category": "security-reliability",
      "canonical_path": "/Users/me/Library/CloudStorage/OneDrive-Personal/Library/assurance/.../Secure by Design.pdf",
      "source": "Assurance Calibre",
      "size": 1234567,
      "created_at": "2026-07-14T12:00:00+00:00"
    }
  ]
}
```

Additional fields are ignored.

## Safety Notes

- Normal browsing does not modify Calibre metadata.
- Fetching a book copies one PDF into the local cache.
- Deleting a cached book removes only the local cached copy.
- `bookrefresh` copies only index files from OneDrive to local disk.
- Publishing indexes with `rclone copy` writes only `index.html` and `manifest.json` when the filters above are used.
- `booktaxonomy --apply` modifies Calibre tags, but creates a timestamped `metadata.db.lazybooks-backup-*` first.
- Avoid editing a Calibre SQLite database through a remote mount. Use a real local/synced filesystem for Calibre metadata operations.

## License

`lazybooks` is released under the MIT License. See `LICENSE`.

## Versioning

The project version is stored in `VERSION` and exposed by:

```sh
lazybooks --version
```

Git release tags use the same version with a `v` prefix, for example `v0.2.0`.
For a release, update `VERSION`, commit it, tag the commit, and push both:

```sh
git tag v0.2.0
git push
git push origin v0.2.0
```

## Troubleshooting

If `bookrefresh` says the rclone remote is missing, check:

```sh
rclone listremotes
rclone lsf personal-onedrive:
```

If fetch/open fails, confirm `local_prefix` matches the path prefix stored in
the manifest:

```sh
python3 -m json.tool "$HOME/book-indexes/tech/manifest.json" | head
```

If categories look wrong:

1. Check the Calibre tags.
2. Run `booktaxonomy <library>`.
3. Review the CSV.
4. Apply corrected taxonomy tags.
5. Rebuild and publish the index.
