"""Generate the shared contract, including routes implemented by other team members."""

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.core.errors import error_responses
from app.core.security import Admin, StudentWriter
from app.main import API_PREFIX, create_app
from app.routers.sections import TermQuery
from app.schemas.admin import SelectionState
from app.schemas.common import ErrorResponse, ResourceId
from app.schemas.dev import PingResponse, StrategyName, StrategyState
from app.schemas.enrollments import (
    EnrollmentCreated, EnrollmentRequest, TimeConflictResponse, WaitlistCreated,
)
from app.schemas.stats import EnrollmentSeries, HotCourses, StatsOverview

# Mounted only on the temporary app used to generate the snapshot.
planned = APIRouter()
student_errors = error_responses(401, 403, 404, 409, 429)
admin_errors = error_responses(401, 403)


@planned.post(
    "/enrollments",
    tags=["enrollments"],
    status_code=201,
    responses={
        202: {"model": WaitlistCreated, "description": "已加入候选队列"},
        **student_errors,
        **error_responses(423),
        409: {
            "model": TimeConflictResponse | ErrorResponse,
            "description": "TIME_CONFLICT / ALREADY_ENROLLED / OPTIMISTIC_CONFLICT / SECTION_FULL",
        },
    },
)
async def create_enrollment(body: EnrollmentRequest, user: StudentWriter) -> EnrollmentCreated:
    raise NotImplementedError


@planned.delete(
    "/enrollments/{id}", tags=["enrollments"], status_code=204, response_class=Response,
    responses={**student_errors, **error_responses(423)},
)
async def drop_enrollment(id: ResourceId, user: StudentWriter) -> Response:
    raise NotImplementedError


@planned.delete(
    "/waitlist/{id}", tags=["enrollments"], status_code=204, response_class=Response,
    responses=student_errors,
)
async def cancel_waitlist(id: ResourceId, user: StudentWriter) -> Response:
    raise NotImplementedError


@planned.get("/stats/overview", tags=["stats"], responses=admin_errors)
async def stats_overview(user: Admin) -> StatsOverview:
    raise NotImplementedError


@planned.get("/stats/hot-courses", tags=["stats"], responses=admin_errors)
async def hot_courses(user: Admin, limit: Annotated[int, Query(ge=1)] = 10) -> HotCourses:
    raise NotImplementedError


@planned.get("/stats/enrollment-series", tags=["stats"], responses=admin_errors)
async def enrollment_series(
    user: Admin, term: TermQuery, hours: Annotated[int, Query(ge=1)] = 6,
) -> EnrollmentSeries:
    raise NotImplementedError


@planned.post("/dev/selection/open", tags=["dev"], responses=error_responses(404))
async def dev_open_selection() -> SelectionState:
    raise NotImplementedError


@planned.post("/dev/selection/close", tags=["dev"], responses=error_responses(404))
async def dev_close_selection() -> SelectionState:
    raise NotImplementedError


@planned.post("/dev/strategy/{name}", tags=["dev"], responses=error_responses(404))
async def change_strategy(name: StrategyName) -> StrategyState:
    raise NotImplementedError


@planned.get("/dev/ping", tags=["dev"], responses=error_responses(404))
async def ping() -> PingResponse:
    raise NotImplementedError


SNAPSHOT = Path(__file__).resolve().parents[1] / "openapi.json"


def build_contract() -> dict:
    app = create_app()
    app.include_router(planned, prefix=API_PREFIX)
    return app.openapi()


if __name__ == "__main__":
    SNAPSHOT.write_text(
        json.dumps(build_contract(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
