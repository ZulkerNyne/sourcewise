# ADR 0003: Explicit local review decisions and immutable approved snapshots

Status: accepted for Phase 1 milestone 3.

Keep intake immutable and publish a separate private database containing only selected,
explicitly reviewed pages. Updating status flags inside the intake would mix extraction
with approval and weaken the historical evidence trail. Partial approval must not
approve an entire edition. Approved search uses SQL status and edition constraints;
unreviewed inspection remains separate.

A human decision records source PDF/database/manifest hashes, exact per-passage text
hashes, reviewer/time, rights evidence, intended use, metadata checks, text fidelity,
and attribution/translation checks. Draft generation fills hashes, never attestations.
Hash equality detects stale review; it cannot establish rights or reviewer authority.
Keep the source manifest, full review decision and resulting database hashes as audit
artifacts. Withdrawal writes a separate event and blocks later approved searches
without removing prior evidence.

Use local filesystem operator trust for this milestone only. Authenticated reviewer
roles, a transactional publication/revocation registry, independent licensing records,
and signed or externally retained audit events are deferred to the application service.
Do not present local records as authenticated or tamper-proof human approvals.
