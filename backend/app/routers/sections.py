import json
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import text

from app.core.errors import error_responses, not_found
from app.core.security import CurrentUser
from app.db.session import Database
from app.schemas.common import Pagination, ResourceId
from app.schemas.sections import Section, SectionDetail, SectionPage

router = APIRouter(prefix="/sections", tags=["sections"])

TermQuery = Annotated[str, Query(min_length=1, max_length=20)]
DepartmentQuery = Annotated[int, Query(ge=1, le=2**63 - 1)]
KeywordQuery = Annotated[str, Query(max_length=100)]

COURSE_JSON = """jsonb_build_object(
    'id', c.id, 'code', c.code, 'name', c.name, 'credits', c.credits, 'dept', c.dept
)"""
MEETINGS_JSON = """COALESCE((
    SELECT jsonb_agg(jsonb_build_object(
        'weekday', m.weekday, 'start_period', m.start_period, 'end_period', m.end_period
    ) ORDER BY m.weekday, m.start_period, m.end_period, m.id)
    FROM section_meetings m WHERE m.section_id = s.id
), '[]'::jsonb)"""
SECTION_COLUMNS = f"""
    s.id, {COURSE_JSON} AS course, s.term, s.teacher, s.capacity, s.enrolled_count,
    s.capacity - s.enrolled_count AS remaining,
    (SELECT count(*) FROM waitlist_entries w WHERE w.section_id = s.id AND w.status = 'WAITING')
        AS waitlist_count,
    {MEETINGS_JSON} AS meetings
"""
SECTIONS_FROM = "FROM sections s JOIN courses c ON c.id = s.course_id"


async def read_section(db: Database, section_id: int, *, include_archived: bool = False) -> Section:
    visible = "" if include_archived else "AND NOT c.archived"
    row = (
        await db.execute(
            text(f"SELECT {SECTION_COLUMNS} {SECTIONS_FROM} WHERE s.id = :id {visible}"),
            {"id": section_id},
        )
    ).mappings().one_or_none()
    if row is None:
        raise not_found("教学班不存在")
    return Section.model_validate(row)


async def paginated_rows(db, columns, source, filters, params, order, pagination):
    where = " AND ".join(filters) or "TRUE"
    total = (
        await db.execute(text(f"SELECT count(*) {source} WHERE {where}"), params)
    ).scalar_one()
    rows = (
        await db.execute(
            text(f"SELECT {columns} {source} WHERE {where} ORDER BY {order} LIMIT :limit OFFSET :offset"),
            {**params, "limit": pagination.size, "offset": pagination.offset},
        )
    ).mappings().all()
    return rows, total


def add_course_filters(request: Request, filters, params, dept_id, keyword=None):
    if dept_id is not None:
        department = request.app.state.settings.department_names.get(dept_id)
        if department is None:
            filters.append("FALSE")
        else:
            filters.append("c.dept = :department")
            params["department"] = department
    if keyword:
        filters.append("(strpos(lower(c.name), lower(:keyword)) > 0 OR strpos(lower(c.code), lower(:keyword)) > 0)")
        params["keyword"] = keyword


@router.get("")
async def list_sections(
    request: Request,
    user: CurrentUser,
    db: Database,
    pagination: Pagination,
    term: TermQuery,
    dept_id: DepartmentQuery | None = None,
    keyword: KeywordQuery | None = None,
    only_open: bool = False,
) -> SectionPage:
    cache = request.app.state.redis
    cache_key = "course-select:sections:" + json.dumps(
        [term, dept_id, keyword, only_open, pagination.page, pagination.size],
        ensure_ascii=False,
    )
    if cache is not None:
        try:
            cached = await cache.get(cache_key)
            if cached is not None:
                return SectionPage.model_validate_json(cached)
        except (RedisError, ValidationError):
            pass
    filters = ["s.term = :term", "NOT c.archived"]
    params = {"term": term}
    add_course_filters(request, filters, params, dept_id, keyword)
    if only_open:
        filters.append("s.enrolled_count < s.capacity")
    rows, total = await paginated_rows(
        db, SECTION_COLUMNS, SECTIONS_FROM, filters, params, "s.id", pagination,
    )
    result = SectionPage(items=rows, total=total, page=pagination.page, size=pagination.size)
    if cache is not None:
        try:
            await cache.set(cache_key, result.model_dump_json(), ex=5)
        except RedisError:
            pass
    return result


@router.get("/{id}", responses=error_responses(404))
async def section_detail(id: ResourceId, user: CurrentUser, db: Database) -> SectionDetail:
    section = await read_section(db, id)
    return SectionDetail(**section.model_dump())
