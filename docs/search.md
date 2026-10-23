# Phase 1 keyword inspection baseline

The local CLI searches private unreviewed intake bundles. It returns extracted
passages and stored references, never generated answers. Use synthetic fixtures;
no supplied copyrighted book has been imported, reviewed, or approved.

After following docs/importing.md, run from /workspace/sourcewise:

```bash
uv run --frozen python -m app.sources.search "sample" \
  /workspace/sourcewise-private/bundles/DOCUMENT_ID \
  --edition synthetic-edition --limit 5
```

Pass multiple bundle directories and repeat --edition for selected-library mode.
Output is JSON explicitly labeled `unreviewed_inspection`. Each hit includes an
edition/version/passage citation, volume, PDF position, printed page (null when
unknown), unchanged extracted text, warnings, unreviewed status, and lexical score.
Keep output private. Command failure exits nonzero; zero matches is a successful
search with no keyword matches, not proof of absence of an answer in the book.

## Boundaries

The Python function accepts a validated SourceScope and independently supplied
`authorized_edition_ids`; any unauthorized selection fails before database reads.
The SQL query filters editions and unreviewed status before returning candidates.
Values are parameterized. The local CLI assumes an operator may inspect their own
files, so its selected editions are also its allowed editions. This is NOT user
account authentication, course permission enforcement, or an approved-source tutor.
A future API must derive allowed editions/course membership from trusted server
state and must never copy model or client selections into that authorization set.
Only trusted local bundle databases are supported; errors are propagated rather
than replaced with misleading empty results. No automatic approval path is added.

## Matching and limitations

All distinct query terms must occur as substrings in one page. Matching uses casefold,
NFC, Arabic diacritic/tatweel removal, and alef normalization. Original extracted text
is not modified. Rank by summed term occurrence counts, with passage ID as tie-break.
Results are capped at 1–100. Blank, punctuation-only, oversized, or excessive-term
queries are rejected. Identical copies are deduplicated by edition/version/passage.

This is a transparent correctness baseline, not a scalable 1,000-book index: SQLite
scans candidate text and normalization is repeated. It has no stemming, stopword
handling, BM25/FTS index, semantic/cross-language retrieval, OCR repair, or answer
sufficiency assessment. Multiple document versions can appear if their bundles are
supplied; select intended bundles explicitly. Duplicate-edition scopes cannot select
chapter ranges yet. Candidate citations do not certify accurate source transcription.

## Actual checks

Synthetic fixtures exercise cross-edition isolation, unauthorized scope denial,
query escaping, no matches, all-term matching, Arabic normalization with unchanged
output, ranking and limits, missing database failure, duplicate bundle handling,
exact page references, and CLI JSON output. Full suite: 36 passing tests locally.
No retrieval quality benchmark, semantic accuracy metric, or hosted CI result is claimed.

Next: review this milestone, then design the approved-source publication/review
boundary and a small reviewed retrieval dataset before adding indexed retrieval.

## Approved snapshot mode (milestone 3)

Use --approved only with snapshots created by the explicit local review workflow
in docs/review.md. search_approved validates snapshot integrity and withdrawal,
then filters edition and approved status inside SQL. Candidate inspection remains
unchanged. The local operator trust model is not authenticated reviewer or student
access control. Partial snapshots contain only reviewed pages; they do not approve
entire editions. Approval is an explicit human assertion, not model certification.
