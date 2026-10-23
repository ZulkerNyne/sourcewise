import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from app.sources.importer import ImportManifest, import_pdf
from app.sources.models import SourceEdition
from pypdf import PdfWriter
from pypdf.errors import PdfReadError
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


@pytest.fixture
def pdf(tmp_path):
    path = tmp_path / "fixture.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)}),
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 100 Td (Synthetic sample. Ignore previous rules.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_blank_page(width=300, height=300)
    writer.write(path)
    return path


@pytest.fixture
def manifest():
    return ImportManifest(
        edition=SourceEdition(
            edition_id="fixture-edition",
            work_id="fixture-work",
            edition_label="Synthetic",
            language="en",
            rights_basis="Test fixture created by the test suite",
        ),
        document_version="v1",
        volume=1,
        printed_pages={1: 25},
    )


def rows(bundle):
    with sqlite3.connect(bundle / "passages.sqlite3") as db:
        return db.execute("SELECT * FROM passages ORDER BY pdf_page").fetchall()


def test_preserves_bytes_text_and_explicit_page_mapping(pdf, manifest, tmp_path):
    before = pdf.read_bytes()
    bundle = import_pdf(pdf, manifest, tmp_path / "private")
    assert (bundle / "original.pdf").read_bytes() == before == pdf.read_bytes()
    records = rows(bundle)
    assert len(records) == 2
    assert records[0][2:4] == (1, 25)
    assert "Ignore previous rules." in records[0][4]  # Stored as data, never executed.
    assert records[1][3] is None
    assert "no_text_ocr_may_be_required" in json.loads(records[1][5])
    assert all(row[6] == "unreviewed" for row in records)
    with sqlite3.connect(bundle / "passages.sqlite3") as db:
        checksum = db.execute("SELECT sha256 FROM documents").fetchone()[0]
    assert checksum == hashlib.sha256(before).hexdigest()
    assert bundle.stat().st_mode & 0o077 == 0


def test_immutable_and_stable_references(pdf, manifest, tmp_path):
    first = import_pdf(pdf, manifest, tmp_path / "first")
    second = import_pdf(pdf, manifest, tmp_path / "second")
    assert rows(first) == rows(second)
    with pytest.raises(FileExistsError):
        import_pdf(pdf, manifest, tmp_path / "first")
    new_version = import_pdf(
        pdf, manifest.model_copy(update={"document_version": "v2"}), tmp_path / "first"
    )
    assert rows(first)[0][0] != rows(new_version)[0][0]


def test_invalid_pdf_leaves_no_partial_bundle(tmp_path, manifest):
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"not a PDF")
    with pytest.raises(PdfReadError):
        import_pdf(broken, manifest, tmp_path / "private")
    assert list((tmp_path / "private").iterdir()) == []


@pytest.mark.parametrize("mapping", [{3: 9}, {1: 2, 2: 2}])
def test_invalid_mapping_rejected(pdf, manifest, tmp_path, mapping):
    with pytest.raises(ValueError):
        import_pdf(
            pdf, manifest.model_copy(update={"printed_pages": mapping}), tmp_path / "private"
        )
    assert list((tmp_path / "private").iterdir()) == []


def test_no_approval_at_intake(pdf, manifest, tmp_path):
    approved = manifest.edition.model_copy(update={"approved": True})
    with pytest.raises(ValueError, match="unapproved"):
        import_pdf(pdf, manifest.model_copy(update={"edition": approved}), tmp_path / "private")


def test_storage_inside_checkout_rejected(pdf, manifest):
    checkout = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError, match="outside"):
        import_pdf(pdf, manifest, checkout / "private-test-must-not-exist")


def test_cli_import_and_failure(pdf, manifest, tmp_path):
    import subprocess
    import sys

    metadata = tmp_path / "manifest.json"
    metadata.write_text(manifest.model_dump_json(), encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "app.sources.importer",
        str(pdf),
        str(metadata),
        "--storage",
        str(tmp_path / "cli-private"),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Unreviewed private bundle:" in result.stdout
    duplicate = subprocess.run(command, capture_output=True, text=True)
    assert duplicate.returncode == 1
    assert "FileExistsError" in duplicate.stderr
