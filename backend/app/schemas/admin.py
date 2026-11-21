from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator
from pydantic.json_schema import SkipJsonSchema

from app.schemas.common import Items, Page, ResourceId, Term
from app.schemas.sections import Course, Meeting, Section

CourseCode = Annotated[str, Field(min_length=1, max_length=20)]
CourseName = Annotated[str, Field(min_length=1, max_length=100)]
TeacherName = Annotated[str, Field(min_length=1, max_length=50)]
Credits = Annotated[int, Field(ge=1, le=10)]
Capacity = Annotated[int, Field(ge=1, le=2**31 - 1)]


class PatchRequest(BaseModel):
    @model_validator(mode="after")
    def reject_explicit_nulls(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} 不允许为 null")
        return self


class AdminCourse(Course):
    archived: bool


class CourseCreate(BaseModel):
    code: CourseCode
    name: CourseName
    credits: Credits
    dept_id: ResourceId


class CoursePatch(PatchRequest):
    code: CourseCode | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    name: CourseName | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    credits: Credits | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    dept_id: ResourceId | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    archived: bool | SkipJsonSchema[None] = Field(default_factory=lambda: None)


class AdminSection(Section):
    selection_open: bool


class SectionCreate(BaseModel):
    course_id: ResourceId
    term: Term
    teacher: TeacherName
    capacity: Capacity
    meetings: list[Meeting] = Field(min_length=1)


class SectionPatch(PatchRequest):
    teacher: TeacherName | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    capacity: Capacity | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    meetings: Annotated[list[Meeting], Field(min_length=1)] | SkipJsonSchema[None] = Field(default_factory=lambda: None)


class RosterEntry(BaseModel):
    student_no: str
    name: str
    enrolled_at: datetime
    source: Literal["ENROLL", "PROMOTED"]


class SelectionState(BaseModel):
    selection_open: bool


AdminCoursePage = Page[AdminCourse]
AdminSectionPage = Page[AdminSection]
Roster = Items[RosterEntry]
