from fastapi import APIRouter
from sqlalchemy import text

from app.core.security import Student
from app.db.session import Database
from app.routers.sections import COURSE_JSON, MEETINGS_JSON, TermQuery
from app.schemas.enrollments import MyEnrollments, MyWaitlist, Timetable, TimetableCell

router = APIRouter(prefix="/me", tags=["me"])
COLORS = (
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
)


@router.get("/enrollments")
async def list_my_enrollments(user: Student, db: Database) -> MyEnrollments:
    rows = (
        await db.execute(
            text(f"""
                SELECT e.id AS enrollment_id, s.id AS section_id, {COURSE_JSON} AS course,
                       {MEETINGS_JSON} AS meetings, e.created_at AS enrolled_at
                FROM enrollments e
                JOIN sections s ON s.id = e.section_id
                JOIN courses c ON c.id = s.course_id
                WHERE e.student_id = :student_id AND e.status = 'ACTIVE'
                ORDER BY e.created_at DESC, e.id DESC
            """),
            {"student_id": user.id},
        )
    ).mappings().all()
    return MyEnrollments(items=rows, total=len(rows))


@router.get("/waitlist")
async def list_my_waitlist(user: Student, db: Database) -> MyWaitlist:
    rows = (
        await db.execute(
            text("""
                SELECT w.id, s.id AS section_id, c.name AS course_name,
                       (SELECT count(*) FROM waitlist_entries ahead
                        WHERE ahead.section_id = w.section_id AND ahead.status = 'WAITING'
                          AND ahead.position <= w.position) AS position,
                       s.enrolled_count AS section_enrolled, s.capacity AS section_capacity,
                       w.created_at AS joined_at
                FROM waitlist_entries w
                JOIN sections s ON s.id = w.section_id
                JOIN courses c ON c.id = s.course_id
                WHERE w.student_id = :student_id AND w.status = 'WAITING'
                ORDER BY w.created_at DESC, w.id DESC
            """),
            {"student_id": user.id},
        )
    ).mappings().all()
    return MyWaitlist(items=rows, total=len(rows))


@router.get("/timetable")
async def timetable(user: Student, db: Database, term: TermQuery | None = None) -> Timetable:
    params = {"student_id": user.id}
    if term is None:
        term = (
            await db.execute(
                text("""
                    SELECT coalesce(
                        (SELECT s.term FROM enrollments e JOIN sections s ON s.id = e.section_id
                         WHERE e.student_id = :student_id AND e.status = 'ACTIVE'
                         ORDER BY e.created_at DESC, e.id DESC LIMIT 1),
                        (SELECT s.term FROM sections s ORDER BY s.created_at DESC, s.id DESC LIMIT 1),
                        ''
                    )
                """),
                params,
            )
        ).scalar_one()
    rows = (
        await db.execute(
            text("""
                SELECT s.id AS section_id, c.name AS course_name, m.weekday, m.start_period, m.end_period
                FROM enrollments e
                JOIN sections s ON s.id = e.section_id
                JOIN courses c ON c.id = s.course_id
                JOIN section_meetings m ON m.section_id = s.id
                WHERE e.student_id = :student_id AND e.status = 'ACTIVE' AND s.term = :term
                ORDER BY m.weekday, m.start_period, m.end_period, s.id, m.id
            """),
            {**params, "term": term},
        )
    ).mappings().all()
    return Timetable(
        term=term,
        cells=[TimetableCell(**row, color=COLORS[row["section_id"] % len(COLORS)]) for row in rows],
    )
