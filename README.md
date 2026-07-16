# lazybooks

[![Tests](https://github.com/richlee/lazybooks/actions/workflows/tests.yml/badge.svg)](https://github.com/richlee/lazybooks/actions/workflows/tests.yml)

Lazy terminal access to cloud-hosted book libraries.

`lazybooks` is a small set of command-line tools for browsing generated book
manifests, fetching a selected PDF from an `rclone` remote, and opening it
locally. It is useful on machines where you can authenticate to a cloud provider
through `rclone`, but cannot or do not want to sync the whole library into the
local file manager.

It works best when:

- your PDFs live in cloud storage supported by `rclone`
- you want a small local searchable index, not a full local sync
- you want to download only the book you are about to read
- your library is optionally managed by Calibre, but the browsing UI does not
  need Calibre to be running

The normal workflow is:

1. Keep the source libraries in OneDrive, Google Drive, Dropbox, or another `rclone` provider, optionally managed by Calibre.
2. Generate a small `index.html` and `manifest.json` for each library.
3. Upload those index files to the same provider.
4. Refresh the local manifest cache on any machine.
5. Browse locally and fetch individual PDFs on demand.

For provider-specific setup, see `docs/providers.md`. For category and
taxonomy guidance, see `docs/taxonomy.md`.

## Quick Start: Demo

You can try the TUI without OneDrive, Calibre, or private book data after
installing:

```sh
lazybooks --demo
```

From a source checkout you can also run the explicit demo config:

```sh
git clone https://github.com/richlee/lazybooks.git
cd lazybooks
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/lazybooks --config examples/demo/config.toml
```

The demo data is intentionally tiny and lives in `examples/demo/`. It is useful
for screenshots, testing navigation, switching libraries, search, details, and
cache markers. Opening uncached demo books is expected to fail because the demo
uses a fake `demo:` rclone remote.

On Windows PowerShell, use:

```powershell
git clone https://github.com/richlee/lazybooks.git
cd lazybooks
py -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\lazybooks --config examples/demo/config.toml
```

## Commands

- `lazybooks`: full terminal UI with categories, search, cache state, PDF fetch/open, and cached-copy delete.
- `lazybooks --demo`: run the packaged demo library.
- `lazybooks sync`: build, publish, and refresh all configured libraries.
- `lazybooks doctor`: check dependencies, config, manifests, cache paths, and rclone basics.
- `lazybooks doctor --demo`: check the packaged demo library.
- `lazybooks-doctor`: the same health check as a standalone command.
- `bookrefresh`: copies `index.html` and `manifest.json` from configured cloud providers into a local cache.
- `bookfind`: searches a manifest from the command line and fetches one selected PDF.
- `bookpick`: uses `fzf` as a fast picker and fetches one selected PDF.
- `bookindex`: builds `index.html` and `manifest.json` for a folder of PDFs.
- `booktaxonomy`: proposes and optionally applies cleaner Calibre taxonomy tags.

## Dependencies

Required:

- Python 3.11 or newer
- `rclone`, for real cloud-backed libraries
- a configured `rclone` remote for your cloud storage
- Textual, installed through the Python package metadata

Optional:

- `fzf` for `bookpick`
- Calibre, if you want Calibre-managed metadata and tags

On macOS with Homebrew:

```sh
brew install rclone fzf
```

On Windows, install Python from python.org or the Microsoft Store, then install
`rclone` from <https://rclone.org/downloads/> or a package manager such as
WinGet:

```powershell
winget install Rclone.Rclone
```

## Install As A Product

The recommended user install is `pipx`, because it gives `lazybooks` its own
Python environment while exposing the commands on your `PATH`:

```sh
pipx install lazybooks
lazybooks --version
lazybooks --demo
lazybooks doctor --demo
```

`pipx` installs Python dependencies such as Textual. It does not install system
tools. For a real cloud-backed library you still need:

- `rclone`
- an authenticated `rclone` remote
- `fzf`, only if you want `bookpick`
- Calibre, only if you want Calibre metadata or taxonomy workflows

On macOS:

```sh
brew install pipx rclone fzf
pipx ensurepath
pipx install lazybooks
```

On Windows PowerShell:

```powershell
winget install Python.Python.3.13
winget install Rclone.Rclone
py -m pip install --user pipx
py -m pipx ensurepath
pipx install lazybooks
```

After installing, run:

```sh
lazybooks doctor
```

## Install From A Checkout

Clone the repo and install the package in a virtual environment:

```sh
git clone https://github.com/richlee/lazybooks.git
cd lazybooks
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Use commands through the virtual environment path, or activate it first:

```sh
source .venv/bin/activate
```

The package install provides:

```sh
lazybooks --version
bookrefresh --help
bookfind --help
bookindex --help
booktaxonomy --help
```

For an isolated user install from a checkout:

```sh
pipx install .
```

When working directly from a checkout without installing the package, helper
scripts are also available in `bin/`.

## rclone Setup

Create one or more `rclone` remotes:

```sh
rclone config
```

Typical choices for a personal OneDrive remote:

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

For Google Drive or Dropbox, create additional remotes in the same `rclone config`
flow and choose the relevant storage type. The examples below use
`personal-onedrive:`, `google-drive:`, and `dropbox:`. Use your own remote names
if they differ.

## Configuration

`lazybooks` needs to know four things:

- where downloaded PDFs should be cached locally
- which `rclone` remote can fetch PDFs
- where the small local index files should live
- where those index files are stored in cloud storage

Create `~/.config/lazybooks/config.toml`. A source is normally one `rclone`
remote, such as OneDrive, Google Drive, or Dropbox. Each source can expose one
or more libraries:

On Windows the default config path is `%APPDATA%\lazybooks\config.toml`.
Generated indexes default to `%LOCALAPPDATA%\lazybooks\indexes`, and downloaded
books default to `%LOCALAPPDATA%\lazybooks\cache\books`.

```toml
default_source = "onedrive"
default_library = "assurance"
cache = "~/.cache/lazybooks/books"

[sources.onedrive]
name = "OneDrive"
remote = "personal-onedrive:"
local_prefix = "~/Library/CloudStorage/OneDrive-Personal/"

[sources.onedrive.libraries.assurance]
name = "Assurance"
root = "~/Library/CloudStorage/OneDrive-Personal/Library/assurance/assurance-library-calibre"
title = "Assurance Books"
library_name = "Assurance"
calibre_metadata_only = true
index_dir = "~/.local/share/lazybooks/indexes/onedrive/assurance"
index_remote = "personal-onedrive:Library/book-indexes/assurance"

[sources.onedrive.libraries.tech]
name = "Tech"
root = "~/Library/CloudStorage/OneDrive-Personal/Library/tech/tech-library-calibre"
title = "Tech Books"
library_name = "Tech"
calibre_metadata_only = true
index_dir = "~/.local/share/lazybooks/indexes/onedrive/tech"
index_remote = "personal-onedrive:Library/book-indexes/tech"

[sources.onedrive.libraries.personal]
name = "Personal"
root = "~/Library/CloudStorage/OneDrive-Personal/Library/personal/personal-library-calibre"
title = "Personal Books"
library_name = "Personal"
calibre_metadata_only = true
index_dir = "~/.local/share/lazybooks/indexes/onedrive/personal"
index_remote = "personal-onedrive:Library/book-indexes/personal"

[sources.google]
name = "Google Drive"
remote = "google-drive:"
local_prefix = "~/Library/CloudStorage/GoogleDrive-you@example.com/My Drive/"

[sources.google.libraries.assurance]
name = "Assurance"
root = "~/Library/CloudStorage/GoogleDrive-you@example.com/My Drive/Library/assurance"
title = "Google Assurance Books"
library_name = "Assurance"
index_dir = "~/.local/share/lazybooks/indexes/google/assurance"
index_remote = "google-drive:Library/book-indexes/assurance"

[sources.dropbox]
name = "Dropbox"
remote = "dropbox:"
local_prefix = "~/Library/CloudStorage/Dropbox/"

[sources.dropbox.libraries.assurance]
name = "Assurance"
root = "~/Library/CloudStorage/Dropbox/Library/assurance"
title = "Dropbox Assurance Books"
library_name = "Assurance"
index_dir = "~/.local/share/lazybooks/indexes/dropbox/assurance"
index_remote = "dropbox:Library/book-indexes/assurance"
```

Important fields:

- `default_source`: the cloud/source opened first by `lazybooks`.
- `default_library`: the library opened first within the default source.
- `cache`: where downloaded PDFs are stored locally.
- `sources.<key>.remote`: the `rclone` remote used to fetch PDFs for that source.
- `sources.<key>.local_prefix`: the local filesystem prefix stored in generated manifests for that source.
- `root`: the local folder `bookindex` scans to generate `index.html` and `manifest.json`.
- `title`: the browser title used in `index.html`.
- `library_name`: the source label used for non-Calibre PDFs.
- `calibre_metadata_only`: only index PDFs recorded in Calibre metadata when `true`.
- `index_dir`: where each library's small local `index.html` and `manifest.json` live.
- `index_remote`: where those index files live in the configured cloud provider.

The TUI shows configured sources on the first row and libraries for the selected
source on the second row. Press the displayed source letter, such as `a` or `b`,
to switch provider. Press `1` to `9` to switch library within the active source.

`local_prefix` matters because manifests store local-looking paths such as:

```text
/Users/me/Library/CloudStorage/OneDrive-Personal/Library/tech/...
```

`lazybooks` rewrites that prefix to the configured remote when fetching:

```text
personal-onedrive:Library/tech/...
```

If multiple sources use the same library key, use the source-qualified form in
CLI commands:

```sh
bookindex --library onedrive.assurance --publish
bookrefresh google.assurance
bookfind --library dropbox.assurance security
```

Bare names such as `assurance` still work when they are unique. When a bare name
is ambiguous, the tools print the available `source.library` names.

The cache root is shared by default, but cached PDFs are stored beneath
source/library subdirectories such as
`~/.cache/lazybooks/books/onedrive/assurance/`. That keeps duplicate titles from
different providers or libraries separate.

An example config is included at `examples/config.toml`.

Environment variables such as `LAZYBOOKS_REMOTE` can override some config values,
but a config file is easier for multi-library and multi-provider use. Older flat
configs with a top-level `[libraries]` table are still supported.

Use a different config file for testing or demos:

```sh
lazybooks --demo
lazybooks --config examples/demo/config.toml
bookfind --config examples/demo/config.toml secure
```

## Set Up A Real Library

A real library has a few important locations:

- the source PDFs, usually somewhere in a configured cloud provider
- the generated index folder, usually small enough to keep local
- the published index folder in the same cloud provider
- the local cache for downloaded PDFs

For example:

```text
OneDrive/Library/tech/tech-library-calibre/       # source PDFs and Calibre metadata
~/.local/share/lazybooks/indexes/tech/            # generated index.html and manifest.json
OneDrive/Library/book-indexes/tech/               # published copy of the generated index
~/.cache/lazybooks/books/                         # downloaded PDFs on this machine
```

The generated index is deliberately separate from the PDF library. That keeps
refreshes small and avoids accidentally copying a whole library to a laptop.

## Build An Index

`bookindex` writes two files:

- `index.html`: a simple browser-friendly index.
- `manifest.json`: the data used by `lazybooks`, `bookfind`, and `bookpick`.

For a Calibre-backed library:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/tech-library-calibre" \
  --index-dir "$HOME/.local/share/lazybooks/indexes/tech" \
  --title "Tech Books" \
  --library-name Tech \
  --calibre-metadata-only \
  --local-prefix "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/" \
  --remote "personal-onedrive:Library/tech/"
```

With `--calibre-metadata-only`, `bookindex` indexes PDFs referenced by Calibre's
`metadata.db`, and uses Calibre title, author, and first tag as the browsing
category.

For a folder of PDFs without Calibre metadata:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/reference-pdfs" \
  --index-dir "$HOME/.local/share/lazybooks/indexes/reference" \
  --title "Reference Books" \
  --library-name Reference \
  --category-depth 2 \
  --local-prefix "$HOME/Library/CloudStorage/OneDrive-Personal/Library/reference-pdfs/" \
  --remote "personal-onedrive:Library/reference-pdfs/"
```

For non-Calibre folders, categories come from folder names. `--category-depth 2`
uses the first two path components under the root.

If each configured library has a `root`, build all configured indexes with:

```sh
bookindex --all
```

The usual configured workflow is:

```sh
lazybooks sync
```

That runs `bookindex --all --publish`, then `bookrefresh --all`, so the local
machine has freshly generated manifests and the cloud copy is ready for other
machines.

Build one configured library with:

```sh
bookindex --library onedrive.tech
```

Build and publish configured libraries in one step:

```sh
bookindex --all --publish
bookindex --library google.assurance --publish
```

Publishing uploads only `index.html` and `manifest.json` to each library's
configured `index_remote`.

When `--local-prefix` and `--remote` are supplied, the manifest includes
`remote_path` for each matching book. That is preferred for cross-platform use
because `lazybooks` can fetch directly from the cloud path without relying on
the same local folder prefix on every machine.

## Publish The Index

After building an index, upload only the small index files:

```sh
rclone copy "$HOME/.local/share/lazybooks/indexes/tech" \
  personal-onedrive:Library/book-indexes/tech \
  --filter '+ index.html' \
  --filter '+ manifest.json' \
  --filter '- *'
```

Repeat for each library you want available from other machines, or use
`bookindex --all --publish` when the libraries are configured in
`~/.config/lazybooks/config.toml`.

Then verify the configured refresh path:

```sh
lazybooks doctor
bookrefresh onedrive.tech
bookrefresh --all
```

`bookrefresh` copies only `index.html` and `manifest.json`. It does not copy
PDFs.

## Browse With The TUI

```sh
lazybooks
```

`lazybooks` is the Textual TUI.

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
~/.cache/lazybooks/books
```

Each configured library gets its own subdirectory under that cache root.

Deleting a cached book only removes the local downloaded copy. It does not touch
OneDrive, Calibre, or the manifest.

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

## Taxonomies

The TUI categories come from each book's `category` field in `manifest.json`.
For Calibre-backed libraries, `bookindex` currently derives that category from
the first Calibre tag on the book.

See `docs/taxonomy.md` for the full Calibre and non-Calibre workflows.

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
booktaxonomy onedrive.tech onedrive.personal
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

The classifier is deliberately simple and rules-based. The bundled defaults live
in `lazybooks/default_taxonomy.toml`; copy the relevant parts to
`~/.config/lazybooks/taxonomy.toml` when you want local customisation. A small
example is included at `examples/taxonomy.toml`.

Each profile maps ordered keyword rules to categories. Edit those rules when a
category is too broad, too narrow, or repeatedly wrong:

```toml
[libraries]
"onedrive.tech" = "tech"

[profiles.tech]
manual_review_category = "tech-manual-review"

[[profiles.tech.rules]]
category = "cloud-devops-platform"
keywords = ["kubernetes", "docker", "terraform", "devops", "cloud"]
```

Explain the active profile before generating reports:

```sh
booktaxonomy --explain onedrive.tech
```

This is a good place for manual or assistive AI review:

1. Run `booktaxonomy onedrive.tech onedrive.personal`.
2. Review `reports/*-taxonomy-proposal.csv`.
3. Look especially at `*-manual-review`, low-confidence rows, and categories with only one or two books.
4. Ask an assistant or LLM to propose a smaller controlled taxonomy from the CSV, but check the result yourself.
5. Update `~/.config/lazybooks/taxonomy.toml`.
6. Rerun `booktaxonomy` until the category list is useful.

Do not aim for perfect classification. A manual-review bucket is better than
inventing misleading categories from poor metadata.

### Apply Taxonomy Tags To Calibre

When the proposal looks good:

```sh
booktaxonomy onedrive.tech onedrive.personal --apply
```

`--apply` creates a timestamped backup beside each Calibre database:

```text
metadata.db.lazybooks-backup-YYYYMMDD-HHMMSS
```

It then replaces each selected Calibre book's tags with its proposed taxonomy
category. It works on all Calibre book records in the selected libraries, not
just PDFs.

`--apply` requires explicit library names so a multi-provider setup cannot
accidentally update every matching `tech` or `personal` library.

After applying tags, rebuild and publish the affected indexes:

```sh
lazybooks sync
```

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
access to your cloud remotes, Calibre libraries, or personal config.

Before a release, also run:

```sh
.venv/bin/python -m py_compile lazybooks/*.py lazybooks/cli/*.py lazybooks/tui/*.py
.venv/bin/lazybooks --version
```

## Public Readiness

The core v0.2 product is usable, but a more public-facing release still needs:

- cross-platform smoke testing on macOS, Linux, and Windows
- confirmation of `rclone`, path, and file-opening behaviour on each platform
- a short GitHub release note for each tagged release
- a decision on whether to move remaining helper scripts into package entry points

Use `docs/cross-platform-checklist.md` for platform test passes.

### Screenshots And GIFs

Use the demo data so screenshots do not expose a personal library:

```sh
.venv/bin/lazybooks --config examples/demo/config.toml
```

Recommended captures:

- main TUI with Engineering selected and a cached `C` marker visible
- search open with a filtered result set
- Book Details modal
- optional short GIF: switch library, change category, search, open details

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
      "remote_path": "personal-onedrive:Library/assurance/.../Secure by Design.pdf",
      "source": "Assurance Calibre",
      "size": 1234567,
      "created_at": "2026-07-14T12:00:00+00:00"
    }
  ]
}
```

Additional fields are ignored. If `remote_path` is present, `lazybooks` uses it
directly when fetching. If it is absent, `lazybooks` falls back to rewriting
`canonical_path` using the configured `local_prefix` and `remote`.

## Safety Notes

- Normal browsing does not modify Calibre metadata.
- Fetching a book copies one PDF into the local cache.
- Deleting a cached book removes only the local cached copy.
- `bookrefresh` copies only index files from configured cloud providers to local disk.
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

PyPI publishing uses GitHub Actions trusted publishing. Configure PyPI with:

```text
Owner: richlee
Repository name: lazybooks
Workflow name: publish.yml
Environment name: pypi
```

Then publish by creating a GitHub Release from the matching tag. The
`.github/workflows/publish.yml` workflow builds the distributions, checks them
with Twine, and uploads them to PyPI without a stored API token.

## Troubleshooting

If `bookrefresh` says the rclone remote is missing, check:

```sh
rclone listremotes
rclone lsf personal-onedrive:
```

If fetch/open fails, confirm `local_prefix` matches the path prefix stored in
the manifest:

```sh
python3 -m json.tool "$HOME/.local/share/lazybooks/indexes/tech/manifest.json" | head
```

If categories look wrong:

1. Check the Calibre tags.
2. Run `booktaxonomy <library>`.
3. Review the CSV.
4. Apply corrected taxonomy tags.
5. Rebuild and publish the index.
