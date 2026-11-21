from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Page


class Meeting(BaseModel):
    weekday: int = Field(ge=1, le=7)
    start_period: int = Field(ge=1, le=12)
    end_period: int = Field(ge=1, le=12)

    @model_validator(mode="after")
    def validate_order(self):
        if self.start_period > self.end_period:
            raise ValueError("开始节次不能晚于结束节次")
        return self


class Course(BaseModel):
    id: int
    code: str
    name: str
    credits: int
    dept: str


class Section(BaseModel):
    id: int
    course: Course
    term: str
    teacher: str
    capacity: int
    enrolled_count: int
    remaining: int
    waitlist_count: int
    meetings: list[Meeting]


class SectionDetail(Section):
    description: str | None = None
    batch: str | None = None


SectionPage = Page[Section]
