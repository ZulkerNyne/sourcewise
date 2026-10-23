# Local review and approval snapshots — Phase 1 milestone 3

This prototype records explicit human attestations; it does not grant rights or
verify reviewer qualifications. Develop with synthetic documents. The supplied
Darussalam book remains unapproved and has not been imported into application storage.
There is no public publication, website, or authenticated reviewer account here.
"Publish" below means create a private local approved snapshot only.

## Workflow

1. Import a synthetic PDF using docs/importing.md.
2. Inspect candidate text using docs/search.md and compare the selected page with
   the original PDF image. Check metadata, volume, printed page mapping, attribution,
   Arabic fidelity where present, and translation provenance. Verify permission for
   the exact intended use. Metadata suggestions are not proof of rights.
3. Prepare a draft review outside Git using an actual returned passage ID:

```bash
uv run --frozen python -m app.sources.review prepare \
  /workspace/sourcewise-private/bundles/DOCUMENT_ID \
  /workspace/sourcewise-private/reviews/review.json \
  --passage 'DOCUMENT_ID:pdf-1'
```

Repeat --passage for other explicitly checked pages. The draft includes current PDF,
database, manifest, and per-passage text fingerprints, but all attestations are false.
It cannot be published as generated. Blank passages cannot be approved.

4. A qualified, authorized operator edits the PRIVATE draft: supply a unique review_id,
   reviewer identity, actual reviewed_at timestamp with timezone, rights_evidence
   reference, and intended_use. Set metadata_and_page_mappings_checked true only after
   checking them. Each selected page requires text_checked_against_original and
   attribution_and_translation_checked true. Remove pages not approved; leave them
   in intake. Check originals rather than trusting extracted text or a model judge.
   Never change hashes to bypass stale-review failures. Recheck changed material
   against originals and prepare a new review. No credentials belong in these files.
5. Create the approved private snapshot:

```bash
uv run --frozen python -m app.sources.review publish \
  /workspace/sourcewise-private/bundles/DOCUMENT_ID \
  /workspace/sourcewise-private/reviews/review.json \
  --storage /workspace/sourcewise-private/approved
```

Input hashes and document identity must match; passage IDs must exist and be unique,
text nonblank, and exact text hashes current. The original bundle stays unreviewed
and unchanged. A new private snapshot contains ONLY reviewed pages, plus review.json,
source-manifest.json, publication.json, and passages.sqlite3. It references the
original PDF checksum without duplicating the PDF. Keep the original private bundle
for image inspection. Passage IDs and source document versions are preserved.
The copied source manifest remains an intake provenance record, not an edition-wide
approval flag. A partial snapshot never approves the rest of that edition.

6. Search only approved snapshots:

```bash
uv run --frozen python -m app.sources.search "sample" \
  /workspace/sourcewise-private/approved/PUBLICATION_ID \
  --edition synthetic-edition --approved
```

The command verifies snapshot fingerprints, rejects withdrawn publications, and applies
both edition and approved-status constraints in SQL before returning/ranking text.
Unreviewed intake bundles are rejected in approved mode, not silently treated as empty
approved corpora. Default inspection mode still only returns unreviewed candidates.
For future APIs, pass independently server-derived authorized editions to search_approved;
the local CLI's operator selection is not account/course access control.

7. Withdraw a snapshot when rights, text quality, or another review issue changes:

```bash
uv run --frozen python -m app.sources.review withdraw \
  /workspace/sourcewise-private/approved/PUBLICATION_ID \
  --reviewer "Reviewer name" --reason "Reason for withdrawal"
```

An exclusive withdrawal.json records who, when, and why, without deleting review/text
history. Later approved searches fail closed for this snapshot. There is no restore
command; a subsequent independently reviewed decision needs a new review ID. Historical
snapshots are not automatically withdrawn when a different snapshot is created.

## Integrity, audit, and limitations

Fingerprints bind decisions to exact source PDF/database/manifest bytes and text.
Publication records bind the resulting snapshot database and review file. Changed
files fail verification, but hashes are not signatures or a defense against a malicious
operator who can rewrite both data and audit records. Filesystem access is the local
trust boundary; there is no reviewer authentication or immutable external audit log.
Review timestamps/names and evidence are operator assertions. They do not establish
legal permission, Arabic correctness, or theological accuracy by themselves.

Snapshots are private, owner-accessible local files. Errors remove staging output;
existing review IDs are not overwritten. Corrections need a new imported document
version and review; this workflow never silently repairs source text. Page-level review
is provisional segmentation, not a verified translation/alignment data model. No OCR,
public API, course membership enforcement, concurrent multi-user transactions, signed
provenance, or 1,000-book review dashboard is implemented. Publication withdrawal is
checked at search start; production concurrency and in-flight revocation need a
transactional registry before a learner-facing service.

## Tests

Synthetic tests cover partial publication, untouched original intake, exact preserved
references/text, rejection of missing/blank/changed passages and files, required human
attestations, invalid drafts, duplicate review protection, snapshot integrity, approved
versus unreviewed separation, permission denial, withdrawal, and CLI publish/search/
withdraw execution. No real book has been approved by these software tests.
