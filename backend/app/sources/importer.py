"""Private, immutable PDF intake; no approval or retrieval is performed."""

import argparse
import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field
from pypdf import PdfReader

from app.sources.models import Identifier, PositiveInt, Record, SourceEdition


class ImportManifest(Record):
    edition: SourceEdition
    document_version: Identifier
    volume: PositiveInt
    # PDF positions are 1-based. Only explicitly supplied printed labels are stored.
    printed_pages: dict[Annotated[int, Field(gt=0)], PositiveInt] = Field(default_factory=dict)
    review_status: Literal["unreviewed"] = "unreviewed"


def import_pdf(pdf: Path, manifest: ImportManifest, storage: Path) -> Path:
    """Create an immutable private bundle, or fail without publishing partial output.

    Storage must be outside the checkout. Approval is deliberately unsupported.
    Extracted text is a candidate transcription, never certified original wording.
    """
    if manifest.edition.approved:
        raise ValueError("Intake requires an unapproved edition")
    storage = storage.resolve()
    checkout = Path(__file__).resolve().parents[3]
    if storage == checkout or checkout in storage.parents:
        raise ValueError("Private storage must be outside the source checkout")
    storage.mkdir(parents=True, exist_ok=True, mode=0o700)
    identity = json.dumps(
        [manifest.edition.edition_id, manifest.document_version, manifest.volume],
        ensure_ascii=False,
    )
    document_id = hashlib.sha256(identity.encode()).hexdigest()
    destination = storage / document_id
    if destination.exists():
        raise FileExistsError("This edition/version/volume already exists; use a new version")
    staging = Path(tempfile.mkdtemp(prefix=".intake-", dir=storage))
    try:
        original = staging / "original.pdf"
        shutil.copyfile(pdf, original)
        original.chmod(0o600)
        with original.open("rb") as source:
            checksum = hashlib.file_digest(source, "sha256").hexdigest()
        reader = PdfReader(original, strict=True)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported")
        if not reader.pages:
            raise ValueError("PDF has no pages")
        if any(index > len(reader.pages) for index in manifest.printed_pages):
            raise ValueError("Printed page mapping refers to a missing PDF page")
        labels = list(manifest.printed_pages.values())
        if len(set(labels)) != len(labels):
            raise ValueError("Printed page labels must be unique within a volume")
        (staging / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        with sqlite3.connect(staging / "passages.sqlite3") as connection:
            connection.executescript("""
                CREATE TABLE documents (
                    document_id TEXT PRIMARY KEY, edition_id TEXT NOT NULL,
                    document_version TEXT NOT NULL, volume INTEGER NOT NULL,
                    sha256 TEXT NOT NULL, page_count INTEGER NOT NULL,
                    review_status TEXT NOT NULL CHECK(review_status = 'unreviewed')
                );
                CREATE TABLE passages (
                    passage_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(document_id),
                    pdf_page INTEGER NOT NULL CHECK(pdf_page > 0),
                    printed_page INTEGER CHECK(printed_page > 0),
                    extracted_text TEXT NOT NULL, warnings_json TEXT NOT NULL,
                    review_status TEXT NOT NULL CHECK(review_status = 'unreviewed'),
                    UNIQUE(document_id, pdf_page)
                );
            """)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    document_id,
                    manifest.edition.edition_id,
                    manifest.document_version,
                    manifest.volume,
                    checksum,
                    len(reader.pages),
                    "unreviewed",
                ),
            )
            for index, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                warnings = ["human_review_required", "arabic_fidelity_not_verified"]
                if not text.strip():
                    warnings.append("no_text_ocr_may_be_required")
                if "\ufffd" in text:
                    warnings.append("replacement_characters")
                if index not in manifest.printed_pages:
                    warnings.append("printed_page_unmapped")
                connection.execute(
                    "INSERT INTO passages VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"{document_id}:pdf-{index}",
                        document_id,
                        index,
                        manifest.printed_pages.get(index),
                        text,
                        json.dumps(warnings),
                        "unreviewed",
                    ),
                )
        for item in staging.iterdir():
            item.chmod(0o600)
        # A competing completed bundle is nonempty, so rename refuses to overwrite it.
        staging.rename(destination)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import an unapproved PDF into private storage")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--storage", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = ImportManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
        destination = import_pdf(args.pdf, manifest, args.storage)
    except Exception as error:
        # No source text or credentials in command output. Failures never approve content.
        parser.exit(
            1, f"Import failed ({type(error).__name__}); check input and private storage.\n"
        )
    print(f"Unreviewed private bundle: {destination}")


if __name__ == "__main__":
    main()
