"""Synthetic fixtures contain no religious content or approved corpus."""

import pytest
from app.sources.models import Citation, SourceEdition, SourcePassage, SourceScope, SourceWork
from pydantic import ValidationError


def passage(**changes):
    return SourcePassage.model_validate(
        {
            "passage_id": "passage-1",
            "edition_id": "edition-1",
            "document_version": "v1",
            "original_text": "نص تجريبي",
            "language": "ar",
            **changes,
        }
    )


def test_original_text_and_identity_roundtrip():
    record = passage(page=2)
    assert SourcePassage.model_validate_json(record.model_dump_json()) == record
    assert record.original_text == "نص تجريبي"
    assert record.edition_id == "edition-1"


@pytest.mark.parametrize(
    "changes",
    [
        {"passage_id": " "},
        {"edition_id": ""},
        {"document_version": ""},
        {"original_text": "  "},
        {"page": 0},
        {"volume": -1},
        {"page": True},
        {"page": "12"},
        {"unexpected": "field"},
    ],
)
def test_invalid_passages(changes):
    with pytest.raises(ValidationError):
        passage(**changes)


def test_passage_cannot_be_mutated():
    with pytest.raises(ValidationError):
        passage().original_text = "changed"


def test_commentary_requires_distinct_underlying_work():
    work = SourceWork(
        work_id="commentary",
        title="Test",
        author="Fixture",
        kind="commentary",
        underlying_work_id="original",
    )
    assert work.underlying_work_id == "original"
    for parent in (None, "commentary"):
        with pytest.raises(ValidationError):
            SourceWork(
                work_id="commentary",
                title="Test",
                author="Fixture",
                kind="commentary",
                underlying_work_id=parent,
            )


def test_original_cannot_have_commentary_relationship():
    with pytest.raises(ValidationError):
        SourceWork(work_id="a", title="Test", author="Fixture", underlying_work_id="b")


def test_edition_requires_rights_and_defaults_unapproved():
    data = dict(edition_id="e", work_id="w", edition_label="Test", language="ar")
    with pytest.raises(ValidationError):
        SourceEdition(**data)
    assert not SourceEdition(**data, rights_basis="Synthetic test fixture").approved


@pytest.mark.parametrize(
    "changes",
    [
        {"edition_ids": []},
        {"edition_ids": ["e", "e"]},
        {"edition_ids": [""]},
        {"mode": "unrestricted"},
        {"mode": "selected_course"},
        {"course_id": "c"},
    ],
)
def test_invalid_scopes(changes):
    with pytest.raises(ValidationError):
        SourceScope.model_validate({"mode": "selected_book", "edition_ids": ["e"], **changes})


@pytest.mark.parametrize("mode", ["selected_book", "selected_library", "selected_course"])
def test_explicit_scopes(mode):
    scope = SourceScope(
        mode=mode,
        edition_ids=("e", "companion"),
        course_id="course" if mode == "selected_course" else None,
    )
    assert scope.edition_ids == ("e", "companion")


def test_citation_requires_revision_and_disallows_invented_metadata():
    data = dict(passage_id="p", edition_id="e", document_version="v1")
    assert Citation(**data).document_version == "v1"
    with pytest.raises(ValidationError):
        Citation(**{**data, "page": 99})
    del data["document_version"]
    with pytest.raises(ValidationError):
        Citation(**data)
