from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import Items, ResourceId
from app.schemas.sections import Course, Meeting


class EnrollmentRequest(BaseModel):
    section_id: ResourceId
    allow_waitlist: bool = True


class Enrollment(BaseModel):
    id: int
    section_id: int
    course_name: str
    teacher: str
    meetings: list[Meeting]
    enrolled_at: datetime


class WaitlistReceipt(BaseModel):
    id: int
    section_id: int
    position: int
    joined_at: datetime


class EnrollmentCreated(BaseModel):
    status: Literal["ENROLLED"] = "ENROLLED"
    enrollment: Enrollment


class WaitlistCreated(BaseModel):
    status: Literal["WAITLISTED"] = "WAITLISTED"
    waitlist: WaitlistReceipt


class TimeConflict(Meeting):
    with_course_name: str


class TimeConflictDetails(BaseModel):
    conflicts: list[TimeConflict]


class TimeConflictError(BaseModel):
    code: Literal["TIME_CONFLICT"]
    message: str
    details: TimeConflictDetails


class TimeConflictResponse(BaseModel):
    error: TimeConflictError


class EnrolledSection(BaseModel):
    enrollment_id: int
    section_id: int
    course: Course
    meetings: list[Meeting]
    enrolled_at: datetime


class WaitlistItem(WaitlistReceipt):
    course_name: str
    section_enrolled: int
    section_capacity: int


class TimetableCell(Meeting):
    course_name: str
    section_id: int
    color: str


class Timetable(BaseModel):
    term: str
    cells: list[TimetableCell]


MyEnrollments = Items[EnrolledSection]
MyWaitlist = Items[WaitlistItem]
