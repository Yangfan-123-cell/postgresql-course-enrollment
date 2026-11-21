import csv
import io

from fastapi import APIRouter, Request, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ApiError, error_responses, not_found, sqlstate, validation_error
from app.core.security import Admin
from app.db.session import Database
from app.routers.sections import (
    SECTION_COLUMNS,
    SECTIONS_FROM,
    DepartmentQuery,
    KeywordQuery,
    TermQuery,
    add_course_filters,
    paginated_rows,
    read_section,
)
from app.schemas.admin import (
    AdminCourse,
    AdminCoursePage,
    AdminSection,
    AdminSectionPage,
    CourseCreate,
    CoursePatch,
    Roster,
    RosterEntry,
    SectionCreate,
    SectionPatch,
    SelectionState,
)
from app.schemas.common import Pagination, ResourceId
from app.schemas.sections import Meeting

router = APIRouter(prefix="/admin", tags=["admin"])

COURSE_COLUMNS = "c.id, c.code, c.name, c.credits, c.dept, c.archived"
SELECTION_OPEN = """COALESCE((
    SELECT value = 'true' FROM system_config WHERE key = 'selection_open'
), false)"""
ROSTER_FROM = "FROM enrollments e JOIN users u ON u.id = e.student_id"
ROSTER_FILTERS = ["e.section_id = :id", "e.status = 'ACTIVE'"]
ROSTER_ORDER = "u.student_no, e.id"
ROSTER_COLUMNS = """
    u.student_no, u.name, e.created_at AS enrolled_at,
    CASE WHEN EXISTS (
        SELECT 1
        FROM audit_log a
        WHERE a.section_id = e.section_id AND a.action = 'PROMOTE'
          AND a.created_at >= e.created_at
          AND CASE
              WHEN a.after ->> 'enrollment_id' IS NOT NULL THEN a.after ->> 'enrollment_id' = e.id::text
              WHEN a.after ->> 'student_id' IS NOT NULL THEN a.after ->> 'student_id' = e.student_id::text
              ELSE a.actor_id = e.student_id
          END
    ) THEN 'PROMOTED' ELSE 'ENROLL' END AS source
"""


def department_name(request: Request, dept_id: int) -> str:
    name = request.app.state.settings.department_names.get(dept_id)
    if name is None:
        raise validation_error("body.dept_id", "院系不存在")
    return name


def duplicate(message: str) -> ApiError:
    return ApiError(409, "DUPLICATE_RESOURCE", message)


def validate_meetings(meetings: list[Meeting]) -> None:
    ordered = sorted(meetings, key=lambda item: (item.weekday, item.start_period))
    for previous, current in zip(ordered, ordered[1:]):
        if previous.weekday == current.weekday and current.start_period <= previous.end_period:
            raise validation_error("body.meetings", "同一教学班的上课时间不能重叠")


async def insert_meetings(db: Database, section_id: int, meetings: list[Meeting]) -> None:
    await db.execute(
        text("""
            INSERT INTO section_meetings(section_id, weekday, start_period, end_period)
            VALUES (:section_id, :weekday, :start_period, :end_period)
        """),
        [{"section_id": section_id, **meeting.model_dump()} for meeting in meetings],
    )


async def read_admin_section(db: Database, section_id: int) -> AdminSection:
    section = await read_section(db, section_id, include_archived=True)
    selection_open = (await db.execute(text(f"SELECT {SELECTION_OPEN}"))).scalar_one()
    return AdminSection(**section.model_dump(), selection_open=selection_open)


@router.get("/courses")
async def list_courses(
    request: Request,
    user: Admin,
    db: Database,
    pagination: Pagination,
    keyword: KeywordQuery | None = None,
    dept_id: DepartmentQuery | None = None,
    archived: bool = False,
) -> AdminCoursePage:
    filters = ["c.archived = :archived"]
    params = {"archived": archived}
    add_course_filters(request, filters, params, dept_id, keyword)
    rows, total = await paginated_rows(
        db, COURSE_COLUMNS, "FROM courses c", filters, params, "c.id", pagination,
    )
    return AdminCoursePage(items=rows, total=total, page=pagination.page, size=pagination.size)


@router.post("/courses", status_code=201, responses=error_responses(409))
async def create_course(body: CourseCreate, request: Request, user: Admin, db: Database) -> AdminCourse:
    values = body.model_dump(exclude={"dept_id"})
    values["dept"] = department_name(request, body.dept_id)
    try:
        row = (
            await db.execute(
                text(f"""
                    INSERT INTO courses AS c (code, name, credits, dept)
                    VALUES (:code, :name, :credits, :dept) RETURNING {COURSE_COLUMNS}
                """),
                values,
            )
        ).mappings().one()
        await db.commit()
    except IntegrityError as exc:
        if sqlstate(exc) == "23505":
            raise duplicate("课程号已存在") from exc
        raise
    return AdminCourse.model_validate(row)


@router.patch("/courses/{id}", responses=error_responses(404, 409))
async def patch_course(
    id: ResourceId, body: CoursePatch, request: Request, user: Admin, db: Database,
) -> AdminCourse:
    values = body.model_dump(exclude_unset=True, exclude={"dept_id"})
    if body.dept_id is not None:
        values["dept"] = department_name(request, body.dept_id)
    try:
        if values:
            updates = ", ".join(f"{column} = :{column}" for column in values)
            statement = f"UPDATE courses c SET {updates} WHERE c.id = :id RETURNING {COURSE_COLUMNS}"
        else:
            statement = f"SELECT {COURSE_COLUMNS} FROM courses c WHERE c.id = :id"
        row = (
            await db.execute(text(statement), {**values, "id": id})
        ).mappings().one_or_none()
        if row is None:
            raise not_found("课程不存在")
        await db.commit()
    except IntegrityError as exc:
        if sqlstate(exc) == "23505":
            raise duplicate("课程号已存在") from exc
        raise
    return AdminCourse.model_validate(row)


@router.get("/sections")
async def list_sections(
    request: Request,
    user: Admin,
    db: Database,
    pagination: Pagination,
    term: TermQuery | None = None,
    course_id: DepartmentQuery | None = None,
    dept_id: DepartmentQuery | None = None,
) -> AdminSectionPage:
    filters = []
    params = {}
    if term is not None:
        filters.append("s.term = :term")
        params["term"] = term
    if course_id is not None:
        filters.append("s.course_id = :course_id")
        params["course_id"] = course_id
    add_course_filters(request, filters, params, dept_id)
    rows, total = await paginated_rows(
        db, f"{SECTION_COLUMNS}, {SELECTION_OPEN} AS selection_open",
        SECTIONS_FROM, filters, params, "s.id", pagination,
    )
    return AdminSectionPage(items=rows, total=total, page=pagination.page, size=pagination.size)


@router.post("/sections", status_code=201, responses=error_responses(404, 409))
async def create_section(body: SectionCreate, user: Admin, db: Database) -> AdminSection:
    validate_meetings(body.meetings)
    try:
        section_id = (
            await db.execute(
                text("""
                    INSERT INTO sections (course_id, term, teacher, capacity)
                    VALUES (:course_id, :term, :teacher, :capacity) RETURNING id
                """),
                body.model_dump(exclude={"meetings"}),
            )
        ).scalar_one()
        await insert_meetings(db, section_id, body.meetings)
        result = await read_admin_section(db, section_id)
        await db.commit()
    except IntegrityError as exc:
        state = sqlstate(exc)
        if state == "23505":
            raise duplicate("同一课程在该学期已有教学班") from exc
        if state == "23503":
            raise not_found("课程不存在") from exc
        raise
    return result


@router.patch("/sections/{id}", responses=error_responses(404, 409))
async def patch_section(id: ResourceId, body: SectionPatch, user: Admin, db: Database) -> AdminSection:
    if body.meetings is not None:
        validate_meetings(body.meetings)
    enrolled = (
        await db.execute(
            text("SELECT enrolled_count FROM sections WHERE id = :id FOR UPDATE"),
            {"id": id},
        )
    ).scalar_one_or_none()
    if enrolled is None:
        raise not_found("教学班不存在")
    if body.capacity is not None and body.capacity < enrolled:
        raise ApiError(
            409, "CAPACITY_BELOW_ENROLLED", "容量不能小于已选人数",
            {"enrolled_count": enrolled},
        )

    values = body.model_dump(exclude_unset=True, exclude={"meetings"})
    if values or body.meetings is not None:
        assignments = [f"{column} = :{column}" for column in values]
        assignments.append("version = version + 1")
        await db.execute(
            text(f"UPDATE sections SET {', '.join(assignments)} WHERE id = :id"),
            {**values, "id": id},
        )
    if body.meetings is not None:
        await db.execute(text("DELETE FROM section_meetings WHERE section_id = :id"), {"id": id})
        await insert_meetings(db, id, body.meetings)
    result = await read_admin_section(db, id)
    await db.commit()
    return result


async def require_section(db: Database, section_id: int) -> None:
    exists = (
        await db.execute(text("SELECT 1 FROM sections WHERE id = :id"), {"id": section_id})
    ).scalar_one_or_none()
    if exists is None:
        raise not_found("教学班不存在")


@router.get("/sections/{id}/roster", responses=error_responses(404))
async def list_roster(id: ResourceId, user: Admin, db: Database, pagination: Pagination) -> Roster:
    await require_section(db, id)
    rows, total = await paginated_rows(
        db, ROSTER_COLUMNS, ROSTER_FROM, ROSTER_FILTERS, {"id": id}, ROSTER_ORDER, pagination,
    )
    return Roster(items=rows, total=total)


def csv_text(value: str) -> str:
    if value.startswith(("\t", "\r", "\n")) or value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


@router.get(
    "/sections/{id}/roster.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}, **error_responses(404)},
)
async def export_roster(id: ResourceId, user: Admin, db: Database) -> Response:
    await require_section(db, id)
    rows = (
        await db.execute(
            text(f"""
                SELECT {ROSTER_COLUMNS} {ROSTER_FROM}
                WHERE {' AND '.join(ROSTER_FILTERS)} ORDER BY {ROSTER_ORDER}
            """),
            {"id": id},
        )
    ).mappings().all()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("学号", "姓名", "选课时间", "来源"))
    for row in rows:
        entry = RosterEntry.model_validate(row)
        writer.writerow((
            csv_text(entry.student_no), csv_text(entry.name), entry.enrolled_at.isoformat(), entry.source,
        ))
    return Response(
        output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="section_{id}_roster.csv"'},
    )


async def set_selection(db: Database, selection_open: bool) -> SelectionState:
    await db.execute(
        text("""
            INSERT INTO system_config (key, value) VALUES ('selection_open', :value)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """),
        {"value": "true" if selection_open else "false"},
    )
    await db.commit()
    return SelectionState(selection_open=selection_open)


@router.post("/selection/open")
async def open_selection(user: Admin, db: Database) -> SelectionState:
    return await set_selection(db, True)


@router.post("/selection/close")
async def close_selection(user: Admin, db: Database) -> SelectionState:
    return await set_selection(db, False)
