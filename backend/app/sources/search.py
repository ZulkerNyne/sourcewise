"""Read-only scoped keyword inspection of UNREVIEWED local intake bundles.

This development tool is not learner-facing approved-source retrieval. The caller
must supply an independently authorized edition set; it must never come from a model.
"""

import argparse
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

from app.sources.models import Citation, PositiveInt, Record, SourceScope


class CandidateHit(Record):
    citation: Citation
    volume: PositiveInt
    pdf_page: PositiveInt
    printed_page: PositiveInt | None
    text: str
    warnings: tuple[str, ...]
    score: int
    review_status: str


def normalize(text: str) -> str:
    """Normalize matching only; never change stored/displayed original text.

    Basic Arabic diacritic/tatweel removal and alef normalization are a baseline,
    not stemming, OCR repair, semantic matching, or cross-language retrieval.
    """
    text = unicodedata.normalize("NFC", text).casefold()
    return "".join(
        "ا" if char in "أإآٱ" else char
        for char in text
        if char != "ـ" and not ("\u0600" <= char <= "\u06ff" and unicodedata.combining(char))
    )


def search_candidates(
    bundles: list[Path],
    query: str,
    scope: SourceScope,
    *,
    authorized_edition_ids: frozenset[str],
    limit: int = 5,
) -> list[CandidateHit]:
    """Return all-term lexical matches filtered by edition inside each SQL query.

    Only unreviewed candidate results are exposed. Empty results mean no keyword
    matches, not evidence that a book contains no answer. Missing/corrupt databases
    raise rather than silently producing an apparently successful empty search.
    """
    if not set(scope.edition_ids) <= authorized_edition_ids:
        raise PermissionError("Selection includes an unauthorized edition")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if len(query) > 1000:
        raise ValueError("query exceeds 1000 characters")
    terms = sorted(set(re.findall(r"[^\W_]+", normalize(query))))
    if not terms or len(terms) > 32:
        raise ValueError("Provide between 1 and 32 keyword terms")
    placeholders = ",".join("?" for _ in scope.edition_ids)
    predicates = " AND ".join("instr(normalize(p.extracted_text), ?) > 0" for _ in terms)
    score_sql = " + ".join(
        "(length(normalize(p.extracted_text)) - "
        "length(replace(normalize(p.extracted_text), ?, ''))) / length(?)"
        for _ in terms
    )
    # Only placeholder counts and fixed SQL fragments are interpolated, never user text.
    sql = f"""
        SELECT p.passage_id, d.edition_id, d.document_version, d.volume,
               p.pdf_page, p.printed_page, p.extracted_text, p.warnings_json,
               p.review_status, {score_sql} AS score
        FROM passages p JOIN documents d ON p.document_id = d.document_id
        WHERE d.edition_id IN ({placeholders})
          AND d.review_status = 'unreviewed' AND p.review_status = 'unreviewed'
          AND {predicates}
        ORDER BY score DESC, p.passage_id ASC LIMIT ?
    """
    hits: dict[tuple[str, str, str], CandidateHit] = {}
    for bundle in dict.fromkeys(path.resolve() for path in bundles):
        database = bundle / "passages.sqlite3"
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
            db.create_function("normalize", 1, normalize, deterministic=True)
            parameters = [term for term in terms for _ in range(2)]
            parameters.extend(scope.edition_ids)
            parameters.extend(terms)
            parameters.append(limit)
            for row in db.execute(sql, parameters):
                (
                    passage_id,
                    edition,
                    version,
                    volume,
                    pdf_page,
                    printed,
                    text,
                    warnings,
                    status,
                    n,
                ) = row
                hit = CandidateHit(
                    citation=Citation(
                        passage_id=passage_id, edition_id=edition, document_version=version
                    ),
                    volume=volume,
                    pdf_page=pdf_page,
                    printed_page=printed,
                    text=text,
                    warnings=tuple(json.loads(warnings)),
                    score=n,
                    review_status=status,
                )
                key = (edition, version, passage_id)
                if key in hits and hits[key] != hit:
                    raise ValueError("Conflicting copies of a passage reference")
                hits[key] = hit
    return sorted(hits.values(), key=lambda hit: (-hit.score, hit.citation.passage_id))[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect UNREVIEWED private keyword matches")
    parser.add_argument("query")
    parser.add_argument("bundles", type=Path, nargs="+")
    parser.add_argument("--edition", action="append", required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    try:
        # A local operator may inspect their own files. This is not server authorization.
        scope = SourceScope(mode="selected_library", edition_ids=tuple(args.edition))
        hits = search_candidates(
            args.bundles,
            args.query,
            scope,
            authorized_edition_ids=frozenset(args.edition),
            limit=args.limit,
        )
    except Exception as error:
        parser.exit(1, f"Search failed ({type(error).__name__}); check scope and bundle files.\n")
    print(
        json.dumps(
            {
                "mode": "unreviewed_inspection",
                "hits": [hit.model_dump(mode="json") for hit in hits],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
