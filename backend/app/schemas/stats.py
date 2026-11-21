from datetime import datetime

from pydantic import BaseModel


class StatsOverview(BaseModel):
    total_enrollments: int
    open_sections: int
    avg_utilization: float
    waitlist_total: int
    selection_open: bool


class HotCourse(BaseModel):
    course_name: str
    picks: int


class HotCourses(BaseModel):
    items: list[HotCourse]


class EnrollmentPoint(BaseModel):
    ts: datetime
    count: int


class EnrollmentSeries(BaseModel):
    points: list[EnrollmentPoint]
