from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from redis.asyncio import Redis

from app.core.config import Settings
from app.core.errors import error_responses, register_error_handlers
from app.core.redis import RateLimiter
from app.db.session import create_database
from app.routers import admin, auth, me, sections

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = settings or Settings()
        engine, sessions = create_database(config)
        cache = None
        if config.redis_url is not None:
            cache = Redis.from_url(
                config.redis_url.get_secret_value(), socket_timeout=0.5, socket_connect_timeout=0.5,
            )
        app.state.settings = config
        app.state.sessions = sessions
        app.state.redis = cache
        app.state.login_limiter = RateLimiter(cache, "login", limit=5, window=60)
        app.state.student_write_limiter = RateLimiter(cache, "student-write", limit=5, window=1)
        try:
            yield
        finally:
            if cache is not None:
                await cache.aclose()
            await engine.dispose()

    app = FastAPI(
        title="Course Enrollment API",
        version="0.1.0",
        lifespan=lifespan,
        responses=error_responses(400, 500, 503),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Content-Disposition", "Retry-After"],
    )
    register_error_handlers(app)
    for router, statuses in (
        (auth.router, (401,)),
        (sections.router, (401,)),
        (me.router, (401, 403)),
        (admin.router, (401, 403)),
    ):
        app.include_router(router, prefix=API_PREFIX, responses=error_responses(*statuses))

    def openapi():
        if app.openapi_schema is None:
            schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
            for methods in schema["paths"].values():
                for operation in methods.values():
                    operation.get("responses", {}).pop("422", None)
            models = schema.get("components", {}).get("schemas", {})
            models.pop("HTTPValidationError", None)
            models.pop("ValidationError", None)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi
    return app


app = create_app()
