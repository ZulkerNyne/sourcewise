# Foundational architecture

Use a modular monolith: separate responsibilities in one deployable application.
Phase 0 implements only Python data contracts. Future modules are source management,
retrieval, evidence assessment, tutor generation, independent verification, learning
management, and evaluation/observability. FastAPI, SQLAlchemy/Alembic, PostgreSQL,
pgvector, and Next.js are planned, not installed or implemented.

Future flow: authenticated request → server-authorized edition scope → database-filtered
retrieval → evidence assessment → extractive response (later structured generation)
→ deterministic citation checks and independent semantic assessment → answer or abstention.
Imported source text is untrusted data, never system instructions. The model cannot
change source permissions. Content approval and ambiguous interpretation need humans.

## Current contracts

A SourceWork identifies the intellectual work and its author. A commentary is a
separate work referencing its underlying work; author attribution stays separate.
SourceEdition identifies a particular edition, its language, publisher when known,
rights basis, and approval state (false by default). Rights text alone is not approval.
SourcePassage identifies original text within an edition and document version,
with optional real page, volume, chapter, and section metadata. Preserve text exactly.
Citation references passage, edition, and version; display metadata must later be
resolved from storage rather than accepted from model-generated labels.
SourceScope holds an explicit, nonempty edition selection for book/course/library
mode. Book companions and course membership need independent server authorization.

Models forbid unexpected fields and mutation; scopes use immutable tuples. They
validate shapes and local invariants, not database existence, membership, licensing,
identity uniqueness, or semantic support. Those checks remain unimplemented.
Published (edition_id, document_version, passage_id) references must stay immutable;
new corrections get new versions, retaining historical records.

Published and machine translations will use separate provenance-bearing records;
no translation or storage model is implemented yet. Arabic originals are never replaced.
See PROJECT_PLAN.md for the complete long-term entity inventory. Do not create all
entities before the milestone that needs them.

## Phase 1 intake prototype

`app.sources.importer` accepts a local PDF, validated edition/volume/version manifest,
and private storage path outside this checkout. It copies the original, extracts
page-level candidate text with pypdf, and publishes an immutable bundle containing
metadata, SHA-256 provenance, and SQLite records. Every page remains unreviewed.
This intentionally separates raw extraction from the approved SourcePassage contract.
SQLite is local intake storage, not a replacement decision for the planned PostgreSQL
application. No approval, retrieval, or learner-facing endpoint exists. See importing.md.

## Phase 1 local keyword inspection

`app.sources.search` reads intake bundles in SQLite read-only mode. It checks the
selected edition set against a caller-provided authorized set, then applies edition
filters inside parameterized SQL before returning candidates. All terms must match;
occurrence count provides a baseline rank. Returned records include immutable citation
identity and explicit unreviewed status. This developer inspection boundary is separate
from planned learner-facing approved retrieval. See search.md for authorization limits.
