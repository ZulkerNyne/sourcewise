# ADR 0001: Python-first modular monolith and source identity contracts

Status: accepted for Phase 0.

Use the proposed backend/app layout and package `app` from backend using Hatchling.
This minimizes divergence from the supplied structure; avoid introducing a second
src tree. uv manages a committed lockfile and editable development installation.
Pydantic provides inspectable validation and eventual API/schema interoperability;
dataclasses alone would require additional boundary validation. Database models
are deferred until storage is needed, avoiding premature migrations and services.

Separate work, edition, and passage identity. Scope selections use edition IDs so
retrieval cannot accidentally mix editions of the same work. Versioned citation
references avoid historical references silently pointing to revised text. Opaque
application-assigned IDs avoid coupling identity to a page number or text hash.
These contracts do not authorize access, prove rights, or verify claims.

Defer FastAPI, PostgreSQL, pgvector, frontend, provider adapters, and embeddings
until required. Open decisions: initial licensed source and qualified reviewer,
translation rights/provenance, identifier issuance, storage constraints, and Arabic
normalization evaluation. Do not select these silently on the user's behalf.
