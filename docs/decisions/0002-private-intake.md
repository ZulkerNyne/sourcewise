# ADR 0002: Immutable local PDF intake bundles

Status: accepted for the first Phase 1 milestone.

Use pypdf for an inspectable, cross-platform baseline without external command
installation. It extracts existing text; it does not OCR images or verify Arabic.
Keep one candidate record per PDF page before introducing reviewed segmentation.
Use SQLite from the standard library for local transactional storage; defer the
PostgreSQL application schema until retrieval/authorization work.

Preserve the original separately from extracted text. Store all candidates unreviewed,
require explicit printed page mapping, and reject replacement of an existing
edition/version/volume. Content hashes establish copied-byte provenance; opaque
hash-based document keys provide stable local reference namespaces, not approval.
Choose a new document version for changed input or extraction. Review and migration
across partial/full PDFs remain manual future work.

Do not import supplied copyrighted editions into application storage without the
source-policy review. Synthetic test PDFs keep implementation independent of licensing.
