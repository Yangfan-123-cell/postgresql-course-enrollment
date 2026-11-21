import json
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.openapi_contract import SNAPSHOT, build_contract

SECRET = "test-key-used-only-by-contract-tests-2026"


def test_reserved_routes_and_responses_in_snapshot():
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot == build_contract()
    paths = snapshot["paths"]
    assert {path.removeprefix("/api/v1") for path in paths} == {
        "/auth/login", "/auth/me", "/sections", "/sections/{id}",
        "/enrollments", "/enrollments/{id}", "/me/enrollments", "/me/waitlist",
        "/waitlist/{id}", "/me/timetable",
        "/admin/courses", "/admin/courses/{id}", "/admin/sections", "/admin/sections/{id}",
        "/admin/sections/{id}/roster", "/admin/sections/{id}/roster.csv",
        "/admin/selection/open", "/admin/selection/close",
        "/stats/overview", "/stats/hot-courses", "/stats/enrollment-series",
        "/dev/selection/open", "/dev/selection/close", "/dev/strategy/{name}", "/dev/ping",
    }
    assert "security" not in paths["/api/v1/auth/login"]["post"]
    assert paths["/api/v1/sections"]["get"]["security"] == [{"HTTPBearer": []}]
    create = paths["/api/v1/enrollments"]["post"]["responses"]
    assert {"201", "202", "400", "409", "423", "429"} <= create.keys()
    assert "content" not in paths["/api/v1/waitlist/{id}"]["delete"]["responses"]["204"]
    csv_response = paths["/api/v1/admin/sections/{id}/roster.csv"]["get"]["responses"]["200"]
    assert "text/csv" in csv_response["content"]
    assert all("422" not in method["responses"] for path in paths.values() for method in path.values())

    actual_paths = create_app().openapi()["paths"]
    assert "/api/v1/sections" in actual_paths
    assert "/api/v1/enrollments" not in actual_paths
    assert "/api/v1/stats/overview" not in actual_paths


def test_authentication_cors_and_connection_errors():
    settings = Settings(
        database_url="postgresql+asyncpg://test:test@127.0.0.1:1/test",
        jwt_secret=SECRET,
        redis_url=None,
    )
    with TestClient(create_app(settings)) as client:
        preflight = client.options(
            "/api/v1/admin/courses",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"

        assert client.get("/api/v1/auth/me").json()["error"]["code"] == "UNAUTHORIZED"
        expired = jwt.encode(
            {"sub": "1", "role": "student", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
            SECRET,
            algorithm="HS256",
        )
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

        bad_request = client.post("/api/v1/auth/login", json={"password": "example"})
        assert bad_request.status_code == 400
        error = bad_request.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["details"]["fields"][0]["field"] == "body.student_no"

        unavailable = client.post("/api/v1/auth/login", json={"student_no": "S0001", "password": "test"})
        assert unavailable.status_code == 503
        assert unavailable.json()["error"]["code"] == "DB_UNAVAILABLE"
