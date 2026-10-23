# Private PDF intake prototype (Phase 1, milestone 1)

This local CLI creates unreviewed candidate transcriptions. It does not approve
content, repair OCR, authorize reuse, search, or generate answers. Use synthetic
material for development until the selected source's rights and review are established.
Do not commit PDFs, private manifests, extracted passages, or source databases.

Create a manifest OUTSIDE the checkout, for example `/workspace/sourcewise-private/manifest.json`:

```json
{
  "edition": {
    "edition_id": "synthetic-edition",
    "work_id": "synthetic-work",
    "edition_label": "Synthetic development fixture",
    "language": "en",
    "rights_basis": "Locally authored synthetic test document",
    "approved": false
  },
  "document_version": "v1",
  "volume": 1,
  "printed_pages": {"1": 25},
  "review_status": "unreviewed"
}
```

From `/workspace/sourcewise`:

```bash
uv sync --frozen
uv run --frozen python -m app.sources.importer /path/to/synthetic.pdf \
  /workspace/sourcewise-private/manifest.json \
  --storage /workspace/sourcewise-private/bundles
```

Supply printed page mappings only after checking the page images. PDF page 1 does
not necessarily mean printed page 1. Unmapped printed pages remain NULL. This
prototype supports positive numeric printed labels, not Roman numerals or ranges.
If using a partial PDF, record its exact identity/version; do not later reuse that
version for a different PDF. Distinct excerpts need distinct document versions.
A future full-volume migration needs explicit reviewed reference mapping.

## Outputs and identity

Each bundle contains `original.pdf` (byte-preserved), `manifest.json`, and
`passages.sqlite3`. Documents record a SHA-256 of the copied original. One candidate
passage is stored per PDF page, including blank pages with warnings. Extracted text
is unchanged, but is NOT verified original text or a SourcePassage approved for use.
Page segmentation avoids pretending the extractor knows paragraph/quotation boundaries.
The immutable document key hashes edition ID, document version, and volume. Passage
IDs append the PDF position. Stable identity depends on never replacing that tuple.
Duplicate imports fail; use a new version for corrections or changed extraction.
Staging is private and removed on failure; completed bundles are never overwritten.
The prototype has no runtime API, model, permission system, or approval operation.

All pages require human review and explicitly warn that Arabic fidelity is unverified.
Blank extraction suggests OCR may be required; replacement characters are flagged.
These heuristics cannot detect all garbling, missing text, reading-order errors, or
meaning changes. Arabic extraction observed in supplied samples remains unsuitable
for automatic approval. No OCR or semantic quality scoring is implemented.

Local staging directories are owner-only and bundle files owner-readable/writable.
This is not encryption or a multi-user security boundary. Use private storage and
backups. Untrusted PDF parsing still needs resource limits and process isolation
before a network upload service is introduced; do not expose this CLI as such a service.

## Validation

Synthetic PDF tests cover byte preservation, extracted text, explicit page mapping,
blank-page warnings, unreviewed state, checksums, stable IDs, version separation,
duplicate protection, invalid input cleanup, and successful/failed CLI invocation.
No supplied book has been imported into application storage or committed.
