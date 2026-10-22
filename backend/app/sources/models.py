"""Source identity contracts, not authorization or semantic verification.

Identifiers are opaque application-assigned strings. Published passage revisions
must remain immutable; a correction receives a new document version.
"""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkKind(StrEnum):
    ORIGINAL = "original"
    COMMENTARY = "commentary"


class SourceWork(Record):
    work_id: Identifier
    title: Text
    author: Text
    kind: WorkKind = WorkKind.ORIGINAL
    underlying_work_id: Identifier | None = None

    @model_validator(mode="after")
    def check_commentary(self) -> Self:
        if (self.kind == WorkKind.COMMENTARY) != (self.underlying_work_id is not None):
            raise ValueError("Only commentaries must reference an underlying work")
        if self.underlying_work_id == self.work_id:
            raise ValueError("A work cannot comment on itself")
        return self


class SourceEdition(Record):
    edition_id: Identifier
    work_id: Identifier
    edition_label: Text
    language: Identifier
    publisher: Text | None = None
    rights_basis: Text
    approved: bool = False


class SourcePassage(Record):
    passage_id: Identifier
    edition_id: Identifier
    document_version: Identifier
    original_text: Text
    language: Identifier
    volume: PositiveInt | None = None
    page: PositiveInt | None = None
    chapter: Text | None = None
    section: Text | None = None


class ScopeMode(StrEnum):
    BOOK = "selected_book"
    COURSE = "selected_course"
    LIBRARY = "selected_library"


class SourceScope(Record):
    """Explicit edition selection; the server must independently authorize it.

    Book scope may include explicitly approved accompanying editions. Course
    membership and accompanying-work relationships require database validation.
    """

    mode: ScopeMode
    edition_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    course_id: Identifier | None = None

    @model_validator(mode="after")
    def check_selection(self) -> Self:
        if len(set(self.edition_ids)) != len(self.edition_ids):
            raise ValueError("Edition selections must be unique")
        if (self.mode == ScopeMode.COURSE) != (self.course_id is not None):
            raise ValueError("Only course scopes must identify a course")
        return self


class Citation(Record):
    """Reference to resolve against stored metadata; never invented page data."""

    passage_id: Identifier
    edition_id: Identifier
    document_version: Identifier
