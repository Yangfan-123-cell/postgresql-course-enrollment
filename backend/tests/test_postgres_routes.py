import asyncio
import csv
import io
import json
import os
from pathlib import Path
from uuid import uuid4

import asyncpg
import bcrypt
import pytest
from fakeredis.aioredis import FakeRedis
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import main
from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "test-password"
SECRET = "another-test-key-only-for-the-postgres-contract-suite"


@pytest.fixture(scope="module")
def database():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL API tests")
    schema = f"api_test_{uuid4().hex}"
    driver_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    ddl = (ROOT / "sql" / "01_schema.sql").read_text(encoding="utf-8")

    async def run_setup():
        connection = await asyncpg.connect(driver_url)
        try:
            await connection.execute(f'CREATE SCHEMA "{schema}"')
            await connection.execute(f'SET search_path TO "{schema}"')
            await connection.execute(ddl)
            password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
            await connection.execute(
                """
                INSERT INTO users(student_no, name, role, major, password_hash)
                VALUES ('S0001', '张三', 'student', '计算机', $1),
                       ('S0002', '李四', 'student', '计算机', $1),
                       ('admin', '管理员', 'admin', '', $1)
                """,
                password_hash,
            )
            await connection.execute(
                """
                INSERT INTO courses(code, name, credits, dept)
                VALUES ('CS301', '操作系统', 4, '计算机'), ('MA101', '高等数学', 4, '数学');

                INSERT INTO sections(course_id, term, teacher, capacity, enrolled_count)
                VALUES (1, '2026-FALL', '赵老师', 2, 2), (2, '2026-FALL', '王老师', 30, 0);

                INSERT INTO section_meetings(section_id, weekday, start_period, end_period)
                VALUES (1, 1, 1, 2), (1, 3, 3, 4);

                INSERT INTO enrollments(student_id, section_id) VALUES (1, 1), (2, 1);
                INSERT INTO audit_log(actor_id, section_id, action, after)
                VALUES (1, 1, 'PROMOTE', '{"enrollment_id": 2, "student_id": 2}');

                INSERT INTO waitlist_entries(student_id, section_id, position, status)
                VALUES (2, 2, 4, 'CANCELLED'), (1, 2, 5, 'WAITING'), (2, 2, 6, 'WAITING');
                """
            )
        finally:
            await connection.close()

    async def cleanup():
        connection = await asyncpg.connect(driver_url)
        try:
            await connection.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        finally:
            await connection.close()

    try:
        asyncio.run(run_setup())
        yield database_url, schema
    finally:
        asyncio.run(cleanup())


@pytest.fixture
def client(database, monkeypatch):
    database_url, schema = database

    def test_engine(settings):
        engine = create_async_engine(
            database_url, connect_args={"server_settings": {"search_path": schema}},
        )
        return engine, async_sessionmaker(engine, expire_on_commit=False)

    monkeypatch.setattr(main, "create_database", test_engine)
    settings = Settings(database_url=database_url, jwt_secret=SECRET, redis_url=None)
    with TestClient(main.create_app(settings), base_url="http://testserver/api/v1/") as api:
        yield api


def login(client, student="S0001", password=PASSWORD):
    return client.post("auth/login", json={"student_no": student, "password": password})


def authorize(client, student="S0001"):
    response = login(client, student)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def test_login_identity_roles_and_rate_limit(client):
    invalid = login(client, "not-found")
    assert_error(invalid, 401, "UNAUTHORIZED")
    assert login(client, "S0001", "wrong").json() == invalid.json()
    response = login(client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["expires_in"] == 43200
    assert body["token_type"] == "bearer"
    assert body["user"] == {"id": 1, "student_no": "S0001", "name": "张三", "role": "student"}
    student = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("auth/me", headers=student).json()["major"] == "计算机"
    assert_error(client.get("admin/courses", headers=student), 403, "FORBIDDEN")
    admin = authorize(client, "admin")
    assert_error(client.get("me/enrollments", headers=admin), 403, "FORBIDDEN")
    assert login(client).status_code == 200
    limited = login(client)
    assert_error(limited, 429, "RATE_LIMITED")
    assert limited.headers["retry-after"] == "60"


def test_browse_filter_pagination_and_detail(client):
    headers = authorize(client)
    assert_error(client.get("sections", headers=headers), 400, "VALIDATION_ERROR")
    assert_error(
        client.get("sections", params={"term": "2026-FALL", "size": 101}, headers=headers),
        400,
        "VALIDATION_ERROR",
    )
    assert_error(client.get("sections/0", headers=headers), 400, "VALIDATION_ERROR")
    params = {"term": "2026-FALL", "size": 1, "keyword": "cs301", "dept_id": 1}
    response = client.get("sections", params=params, headers=headers)
    assert response.status_code == 200, response.text
    section = response.json()["items"][0]
    assert section["course"]["name"] == "操作系统"
    assert section["remaining"] == 0
    assert section["id"] == 1
    assert response.json()["total"] == 1
    assert client.get("sections", params={**params, "page": 2}, headers=headers).json()["items"] == []
    open_sections = client.get(
        "sections", params={"term": "2026-FALL", "only_open": True}, headers=headers,
    ).json()
    assert [item["id"] for item in open_sections["items"]] == [2]
    assert {
        **section, "description": None, "batch": None,
    } == client.get("sections/1", headers=headers).json()
    assert_error(client.get("sections/999", headers=headers), 404, "NOT_FOUND")


def test_personal_queries(client):
    headers = authorize(client)
    enrolled = client.get("me/enrollments", headers=headers).json()
    assert enrolled["total"] == 1
    assert enrolled["items"][0]["enrollment_id"] == 1
    waitlist = client.get("me/waitlist", headers=headers).json()
    assert waitlist["total"] == 1
    assert waitlist["items"][0]["position"] == 1
    assert waitlist["items"][0]["section_id"] == 2
    timetable = client.get("me/timetable", headers=headers).json()
    assert timetable["term"] == "2026-FALL"
    assert [cell["weekday"] for cell in timetable["cells"]] == [1, 3]
    assert len({cell["color"] for cell in timetable["cells"]}) == 1
    assert client.get("me/timetable?term=OTHER", headers=headers).json() == {"term": "OTHER", "cells": []}


def test_admin_course_and_section_writes(client):
    headers = authorize(client, "admin")
    course = {"code": "CS999", "name": "并发数据库", "credits": 3, "dept_id": 1}
    response = client.post("admin/courses", json=course, headers=headers)
    assert response.status_code == 201, response.text
    course_id = response.json()["id"]
    assert response.json()["dept"] == "计算机"
    assert_error(client.post("admin/courses", json=course, headers=headers), 409, "DUPLICATE_RESOURCE")
    assert_error(
        client.patch(f"admin/courses/{course_id}", json={"code": "CS301"}, headers=headers),
        409,
        "DUPLICATE_RESOURCE",
    )

    first = {"weekday": 1, "start_period": 1, "end_period": 2}
    section = {
        "course_id": course_id, "term": "2026-FALL", "teacher": "周老师", "capacity": 10,
        "meetings": [first],
    }
    overlapping = {**section, "meetings": [first, {**first, "start_period": 2}]}
    assert_error(client.post("admin/sections", json=overlapping, headers=headers), 400, "VALIDATION_ERROR")
    response = client.post("admin/sections", json=section, headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    section_id = body["id"]
    assert body["enrolled_count"] == 0
    assert body["meetings"] == [first]
    assert_error(client.post("admin/sections", json=section, headers=headers), 409, "DUPLICATE_RESOURCE")
    assert_error(
        client.post("admin/sections", json={**section, "course_id": 999}, headers=headers),
        404,
        "NOT_FOUND",
    )

    assert_error(
        client.patch("admin/sections/1", json={"capacity": 1}, headers=headers),
        409,
        "CAPACITY_BELOW_ENROLLED",
    )
    updated_meeting = {**first, "weekday": 5}
    updated = client.patch(
        f"admin/sections/{section_id}", json={"capacity": 15, "meetings": [updated_meeting]}, headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["capacity"] == 15
    assert updated.json()["meetings"] == [updated_meeting]
    assert_error(
        client.patch(f"admin/sections/{section_id}", json={"teacher": None}, headers=headers),
        400,
        "VALIDATION_ERROR",
    )

    archived = client.patch(f"admin/courses/{course_id}", json={"archived": True}, headers=headers)
    assert archived.status_code == 200, archived.text
    assert archived.json()["archived"] is True
    visible_to_admin = client.get(
        "admin/courses", params={"archived": True, "dept_id": 1, "keyword": "CS999"}, headers=headers,
    )
    assert visible_to_admin.json()["total"] == 1
    assert_error(client.get(f"sections/{section_id}", headers=headers), 404, "NOT_FOUND")


def test_roster_csv_and_selection_state(client):
    headers = authorize(client, "admin")
    response = client.get("admin/sections/1/roster?size=1&page=2", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["source"] == "PROMOTED"
    response = client.get("admin/sections/1/roster.csv", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == 'attachment; filename="section_1_roster.csv"'
    assert response.content.startswith(b"\xef\xbb\xbf")
    records = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert records[0] == ["学号", "姓名", "选课时间", "来源"]
    assert [record[-1] for record in records[1:]] == ["ENROLL", "PROMOTED"]
    assert_error(client.get("admin/sections/999/roster.csv", headers=headers), 404, "NOT_FOUND")

    for operation, expected in [("open", True), ("close", False)]:
        assert client.post(f"admin/selection/{operation}", headers=headers).json() == {"selection_open": expected}
        listing = client.get("admin/sections", params={"course_id": 1}, headers=headers).json()
        assert listing["items"][0]["selection_open"] is expected


def test_section_cache_uses_five_seconds_and_all_query_parameters(client):
    redis = FakeRedis()
    client.app.state.redis = redis
    try:
        headers = authorize(client)
        params = {
            "term": "2026-FALL", "dept_id": 1, "keyword": "cs301",
            "only_open": False, "page": 1, "size": 1,
        }
        response = client.get("sections", params=params, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 1

        async def set_test_cache_value():
            key = "course-select:sections:" + json.dumps(["2026-FALL", 1, "cs301", False, 1, 1])
            assert 0 < await redis.pttl(key) <= 5000
            await redis.set(key, json.dumps({**response.json(), "total": 99}), keepttl=True)

        client.portal.call(set_test_cache_value)
        assert client.get("sections", params=params, headers=headers).json()["total"] == 99

        alternatives = {
            "term": "OTHER", "dept_id": 3, "keyword": "MA101",
            "only_open": True, "page": 2, "size": 2,
        }
        for name, value in alternatives.items():
            variant = client.get("sections", params={**params, name: value}, headers=headers)
            assert variant.status_code == 200, variant.text
            assert variant.json()["total"] != 99
    finally:
        client.portal.call(redis.aclose)
