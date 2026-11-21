import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException

from app.schemas.common import ErrorResponse, ValidationErrorResponse

logger = logging.getLogger(__name__)

ERROR_DESCRIPTIONS = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "业务冲突",
    423: "SELECTION_CLOSED",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "DB_UNAVAILABLE",
}


def error_responses(*statuses: int):
    return {
        status: {
            "model": ValidationErrorResponse if status == 400 else ErrorResponse,
            "description": ERROR_DESCRIPTIONS[status],
        }
        for status in statuses
    }


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: dict | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details or {}
        self.headers = headers


def validation_error(field: str, message: str) -> ApiError:
    return ApiError(
        400, "VALIDATION_ERROR", "请求参数有误",
        {"fields": [{"field": field, "message": message}]},
    )


def not_found(message: str = "资源不存在") -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


def sqlstate(exc: DBAPIError) -> str:
    return getattr(exc.orig, "sqlstate", "") or ""


def error_response(exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": str(exc), "details": exc.details}},
        headers=exc.headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError):
        return error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(map(str, error["loc"])), "message": error["msg"]}
            for error in exc.errors()
        ]
        return error_response(
            ApiError(400, "VALIDATION_ERROR", "请求参数有误", {"fields": fields})
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        return error_response(
            ApiError(
                exc.status_code,
                ERROR_DESCRIPTIONS.get(exc.status_code, "HTTP_ERROR"),
                str(exc.detail),
                headers=exc.headers,
            )
        )

    @app.exception_handler(DBAPIError)
    async def handle_db_error(request: Request, exc: DBAPIError):
        state = sqlstate(exc)
        if exc.connection_invalidated or state.startswith(("08", "28", "57P0")) or state in {
            "53300", "3D000",
        }:
            return error_response(ApiError(503, "DB_UNAVAILABLE", "数据库暂不可用"))
        logger.error("Unhandled database error for %s (%s)", request.url.path, state)
        return error_response(ApiError(500, "INTERNAL_ERROR", "服务器内部错误"))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.error("Unhandled %s for %s", type(exc).__name__, request.url.path)
        return error_response(ApiError(500, "INTERNAL_ERROR", "服务器内部错误"))
