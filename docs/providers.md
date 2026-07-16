# Cloud Providers

`lazybooks` is cloud-provider neutral at runtime. It shells out to `rclone`, so
the provider boundary is the configured `rclone` remote.

The important fields are:

- `remote`: the rclone remote used to fetch books, such as `personal-onedrive:`
  or `google-drive:`.
- `index_remote`: the rclone path where a library's small `index.html` and
  `manifest.json` are published.
- `local_prefix`: a fallback mapping from paths stored in a manifest to the
  configured remote.
- `remote_path`: an optional per-book manifest field. When present, it is used
  directly and avoids local path rewriting.

## OneDrive

Create the remote:

```sh
rclone config
```

Typical personal OneDrive setup:

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

Smoke test:

```sh
rclone lsf personal-onedrive:
rclone lsf personal-onedrive:"Library"
```

Example config:

```toml
default = "tech"
cache = "~/book-cache"
remote = "personal-onedrive:"
local_prefix = "~/Library/CloudStorage/OneDrive-Personal/"

[libraries.tech]
name = "Tech"
index_dir = "~/book-indexes/tech"
index_remote = "personal-onedrive:Library/book-indexes/tech"
```

Build an index with explicit `remote_path` values:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/tech-library-calibre" \
  --index-dir "$HOME/book-indexes/tech" \
  --title "Tech Books" \
  --library-name Tech \
  --calibre-metadata-only \
  --local-prefix "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/" \
  --remote "personal-onedrive:Library/tech/"
```

## Google Drive

Create the remote:

```sh
rclone config
```

Typical Google Drive setup:

```text
n) New remote
name> google-drive
Storage> drive
client_id>
client_secret>
scope> drive
root_folder_id>
service_account_file>
Edit advanced config? n
Use web browser to automatically authenticate rclone? y
```

Leave `client_id`, `client_secret`, `root_folder_id`, and
`service_account_file` blank unless you have a specific reason to set them.

Smoke test:

```sh
rclone lsf google-drive:
rclone lsf google-drive:"Library"
```

Example config:

```toml
default = "assurance-google"
cache = "~/book-cache"
remote = "google-drive:"
local_prefix = "~/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/"

[libraries.assurance-google]
name = "Assurance Google"
index_dir = "~/book-indexes/assurance-google"
index_remote = "google-drive:Library/book-indexes/assurance"
```

Build an index with explicit `remote_path` values:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Library/assurance" \
  --index-dir "$HOME/book-indexes/assurance-google" \
  --title "Assurance Books" \
  --library-name Assurance \
  --category-depth 2 \
  --local-prefix "$HOME/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Library/assurance/" \
  --remote "google-drive:Library/assurance/"
```

## Prefer `remote_path`

Older manifests can rely on `canonical_path` plus `local_prefix` rewriting.
That works, but it assumes the local path prefix in the manifest matches the
machine running `lazybooks`.

New indexes should pass `--local-prefix` and `--remote` to `bookindex`. That
adds `remote_path` to each manifest item. `lazybooks` then fetches from that
path directly, which is better for:

- using the same index from macOS, Linux, and Windows
- mixing OneDrive and Google Drive libraries
- browser-only or cloud-only machines
- future generated indexes that do not have meaningful local paths

Run:

```sh
lazybooks doctor
```

to confirm the configured remotes exist and manifests are readable.
