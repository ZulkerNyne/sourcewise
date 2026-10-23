"""Explicit human attestations and private approved snapshots (local prototype).

A reviewer name is an operator assertion, not authenticated identity. Hashes bind
review to exact bytes; they do not prove licensing or theological correctness.
"""

import argparse
import hashlib
import json
import shutil
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from app.sources.importer import ImportManifest
from app.sources.models import Identifier, Record, Text

Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class PassageApproval(Record):
    passage_id: Identifier
    text_sha256: Digest
    text_checked_against_original: Literal[True]
    attribution_and_translation_checked: Literal[True]


class ReviewDecision(Record):
    review_id: Identifier
    reviewer: Text
    reviewed_at: AwareDatetime
    source_pdf_sha256: Digest
    source_manifest_sha256: Digest
    source_database_sha256: Digest
    rights_evidence: Text
    intended_use: Text
    metadata_and_page_mappings_checked: Literal[True]
    passages: Annotated[tuple[PassageApproval, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_passages(self) -> "ReviewDecision":
        ids = [passage.passage_id for passage in self.passages]
        if len(ids) != len(set(ids)):
            raise ValueError("Review passage IDs must be unique")
        return self


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def private_storage(storage: Path) -> Path:
    storage = storage.resolve()
    checkout = Path(__file__).resolve().parents[3]
    if storage == checkout or checkout in storage.parents:
        raise ValueError("Approved storage must be outside the checkout")
    storage.mkdir(parents=True, exist_ok=True, mode=0o700)
    return storage


def publish_review(bundle: Path, decision: ReviewDecision, storage: Path) -> Path:
    """Publish only individually reviewed pages; leave intake entirely unchanged."""
    database = bundle / "passages.sqlite3"
    if digest(database) != decision.source_database_sha256:
        raise ValueError("Source database changed since review")
    if digest(bundle / "original.pdf") != decision.source_pdf_sha256:
        raise ValueError("Original PDF changed since review")
    if digest(bundle / "manifest.json") != decision.source_manifest_sha256:
        raise ValueError("Source manifest changed since review")
    manifest = ImportManifest.model_validate_json((bundle / "manifest.json").read_text())
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as source:
        documents = source.execute("SELECT * FROM documents").fetchall()
        if len(documents) != 1:
            raise ValueError("Expected one imported document")
        document = documents[0]
        if (
            document[1:4]
            != (manifest.edition.edition_id, manifest.document_version, manifest.volume)
            or document[4] != decision.source_pdf_sha256
            or document[6] != "unreviewed"
        ):
            raise ValueError("Document identity does not match its original manifest")
        pages = {row[0]: row for row in source.execute("SELECT * FROM passages")}
    selected = []
    for approval in decision.passages:
        row = pages.get(approval.passage_id)
        if row is None or row[1] != document[0] or row[6] != "unreviewed":
            raise ValueError("Review references an unknown or ineligible passage")
        if (
            not row[4].strip()
            or hashlib.sha256(row[4].encode()).hexdigest() != approval.text_sha256
        ):
            raise ValueError("Reviewed text is empty or changed")
        selected.append(row)
    if digest(database) != decision.source_database_sha256:
        raise ValueError("Source database changed during review publication")
    storage = private_storage(storage)
    publication_id = hashlib.sha256(decision.review_id.encode()).hexdigest()
    destination = storage / publication_id
    if destination.exists():
        raise FileExistsError("Review ID has already been published")
    staging = Path(tempfile.mkdtemp(prefix=".review-", dir=storage))
    try:
        with sqlite3.connect(staging / "passages.sqlite3") as target:
            target.executescript("""
                CREATE TABLE documents (
                    document_id TEXT PRIMARY KEY, edition_id TEXT NOT NULL,
                    document_version TEXT NOT NULL, volume INTEGER NOT NULL,
                    sha256 TEXT NOT NULL, page_count INTEGER NOT NULL,
                    review_status TEXT NOT NULL CHECK(review_status = 'approved')
                );
                CREATE TABLE passages (
                    passage_id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                    pdf_page INTEGER NOT NULL, printed_page INTEGER,
                    extracted_text TEXT NOT NULL, warnings_json TEXT NOT NULL,
                    review_status TEXT NOT NULL CHECK(review_status = 'approved'),
                    FOREIGN KEY(document_id) REFERENCES documents(document_id),
                    UNIQUE(document_id, pdf_page)
                );
            """)
            target.execute("PRAGMA foreign_keys=ON")
            target.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)", (*document[:6], "approved")
            )
            for row in selected:
                # Preserve extraction warnings as history; approval doesn't erase them.
                target.execute(
                    "INSERT INTO passages VALUES (?, ?, ?, ?, ?, ?, ?)", (*row[:6], "approved")
                )
        (staging / "review.json").write_text(decision.model_dump_json(indent=2), encoding="utf-8")
        shutil.copyfile(bundle / "manifest.json", staging / "source-manifest.json")
        audit = {
            "review_id": decision.review_id,
            "created_at": datetime.now(UTC).isoformat(),
            "database_sha256": digest(staging / "passages.sqlite3"),
            "review_sha256": digest(staging / "review.json"),
        }
        (staging / "publication.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        for file in staging.iterdir():
            file.chmod(0o600)
        staging.rename(destination)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def verify_publication(bundle: Path) -> None:
    """Reject withdrawn, corrupt or modified publications before text retrieval."""
    if (bundle / "withdrawal.json").exists():
        raise PermissionError("Publication was withdrawn")
    audit = json.loads((bundle / "publication.json").read_text())
    if digest(bundle / "passages.sqlite3") != audit["database_sha256"]:
        raise ValueError("Published database changed")
    if digest(bundle / "review.json") != audit["review_sha256"]:
        raise ValueError("Review record changed")
    decision = ReviewDecision.model_validate_json((bundle / "review.json").read_text())
    if decision.review_id != audit["review_id"]:
        raise ValueError("Publication review identity mismatch")


def withdraw_publication(bundle: Path, reviewer: str, reason: str) -> None:
    if not reviewer.strip() or not reason.strip():
        raise ValueError("Reviewer and reason are required")
    verify_publication(bundle)
    # Exclusive creation preserves the first withdrawal and does not alter approved text.
    with (bundle / "withdrawal.json").open("x", encoding="utf-8") as output:
        (bundle / "withdrawal.json").chmod(0o600)
        json.dump(
            {"reviewer": reviewer, "reason": reason, "withdrawn_at": datetime.now(UTC).isoformat()},
            output,
            indent=2,
        )


def prepare_review(bundle: Path, passage_ids: list[str], output: Path) -> None:
    """Write an intentionally invalid-for-publication draft with unchecked attestations."""
    if not passage_ids or len(set(passage_ids)) != len(passage_ids):
        raise ValueError("Select unique passage IDs")
    with sqlite3.connect(
        (bundle / "passages.sqlite3").resolve().as_uri() + "?mode=ro", uri=True
    ) as source:
        pages = {
            row[0]: row[1]
            for row in source.execute(
                "SELECT passage_id, extracted_text FROM passages WHERE review_status='unreviewed'"
            )
        }
    approvals = []
    for passage_id in passage_ids:
        if passage_id not in pages or not pages[passage_id].strip():
            raise ValueError("Choose existing nonempty unreviewed pages")
        approvals.append(
            {
                "passage_id": passage_id,
                "text_sha256": hashlib.sha256(pages[passage_id].encode()).hexdigest(),
                "text_checked_against_original": False,
                "attribution_and_translation_checked": False,
            }
        )
    draft = {
        "review_id": "",
        "reviewer": "",
        "reviewed_at": datetime.now(UTC).isoformat(),
        "source_pdf_sha256": digest(bundle / "original.pdf"),
        "source_database_sha256": digest(bundle / "passages.sqlite3"),
        "source_manifest_sha256": digest(bundle / "manifest.json"),
        "rights_evidence": "",
        "intended_use": "",
        "metadata_and_page_mappings_checked": False,
        "passages": approvals,
    }
    private_storage(output.parent)
    with output.open("x", encoding="utf-8") as target:
        output.chmod(0o600)
        json.dump(draft, target, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local human review publication and withdrawal")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("bundle", type=Path)
    prepare.add_argument("output", type=Path)
    prepare.add_argument("--passage", action="append", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("bundle", type=Path)
    publish.add_argument("decision", type=Path)
    publish.add_argument("--storage", required=True, type=Path)
    withdraw = commands.add_parser("withdraw")
    withdraw.add_argument("bundle", type=Path)
    withdraw.add_argument("--reviewer", required=True)
    withdraw.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare_review(args.bundle, args.passage, args.output)
            print("Draft created with unchecked attestations; human review is required")
        elif args.command == "publish":
            decision = ReviewDecision.model_validate_json(args.decision.read_text())
            result = publish_review(args.bundle, decision, args.storage)
            print(f"Private approved snapshot: {result}")
        else:
            withdraw_publication(args.bundle, args.reviewer, args.reason)
            print("Publication withdrawn; source and review history retained")
    except Exception as error:
        parser.exit(1, f"Review operation failed ({type(error).__name__}).\n")


if __name__ == "__main__":
    main()
