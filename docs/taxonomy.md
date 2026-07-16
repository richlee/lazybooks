# Taxonomy

`lazybooks` categories are intentionally simple. The TUI groups books by the
`category` field in `manifest.json`.

Where that field comes from depends on how the index was built.

## Calibre-Backed Libraries

For Calibre libraries, `bookindex --calibre-metadata-only` reads `metadata.db`
and uses:

- Calibre title
- Calibre authors
- the first Calibre tag as `category`
- Calibre's known PDF file path

This gives good title and author metadata, but Calibre tags can be noisy:

```text
self
tech
MEAP V14
SEL031000
one-off event names
publisher categories
```

`booktaxonomy` helps clean that up. It reads refreshed manifests, finds the
matching Calibre databases, reviews title, author, existing tags, and comments,
then writes reports:

```sh
bookrefresh tech
booktaxonomy tech
```

Output:

```text
reports/taxonomy-proposal.md
reports/tech-taxonomy-proposal.csv
```

The CSV contains:

- current Calibre tags
- recurring tags, excluding one-off noise
- proposed category
- confidence
- reason

Review the CSV before applying. The classifier is a rules-based assistant, not
an authority.

When the proposal is good enough:

```sh
booktaxonomy tech --apply
```

`--apply` backs up each `metadata.db` before replacing book tags:

```text
metadata.db.lazybooks-backup-YYYYMMDD-HHMMSS
```

After applying taxonomy tags, rebuild and publish the index:

```sh
bookindex \
  --root "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/tech-library-calibre" \
  --index-dir "$HOME/book-indexes/tech" \
  --title "Tech Books" \
  --library-name Tech \
  --calibre-metadata-only \
  --local-prefix "$HOME/Library/CloudStorage/OneDrive-Personal/Library/tech/" \
  --remote "personal-onedrive:Library/tech/"

rclone copy "$HOME/book-indexes/tech" \
  personal-onedrive:Library/book-indexes/tech \
  --filter '+ index.html' \
  --filter '+ manifest.json' \
  --filter '- *'

bookrefresh tech
```

## Non-Calibre Libraries

Non-Calibre libraries still work, but metadata is weaker.

When `bookindex` scans a folder of PDFs without Calibre metadata:

- title and author come from the filename
- `Title - Author.pdf` works best
- files without ` - ` use the filename stem as title and `Unknown` as author
- categories come from folder names
- `--category-depth` controls how much folder path becomes the category

Example:

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

Folder shape:

```text
assurance/
  architecture/security/Secure by Design - Dan Bergh Johnsson.pdf
  delivery/testing/Specification by Example - Gojko Adzic.pdf
```

With `--category-depth 2`, those become:

```text
architecture-security
delivery-testing
```

With `--category-depth 1`, they become:

```text
architecture
delivery
```

## What Taxonomy Can And Cannot Do Without Calibre

`booktaxonomy --apply` is Calibre-specific. It modifies Calibre tags in
`metadata.db`, so it cannot apply tags to a plain folder of PDFs.

For non-Calibre libraries, the practical taxonomy controls are:

- folder structure
- `--category-depth`
- filename cleanup
- future manifest-editing or sidecar-metadata tooling

The current best approach is to make folder names intentional and keep the
taxonomy shallow. Avoid creating hundreds of one-book folders.

Useful folder/category names are broad but not vague:

```text
security-reliability
software-architecture-design
cloud-devops-platform
delivery-testing
governance-assurance
```

Less useful names are either too broad or too specific:

```text
computing
misc
pdfs
2024 downloads
single event or course names
```

## Recommended Workflow

For Calibre libraries:

1. Build index from Calibre metadata.
2. Run `booktaxonomy`.
3. Review the CSV.
4. Apply taxonomy tags when the proposal is acceptable.
5. Rebuild and publish the index.

For non-Calibre libraries:

1. Organise folders into a small taxonomy.
2. Name files as `Title - Author.pdf` where possible.
3. Build index with `--category-depth`.
4. Review the generated HTML/TUI categories.
5. Adjust folders or depth and rebuild.
