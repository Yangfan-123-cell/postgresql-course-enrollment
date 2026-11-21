from datetime import datetime, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.session import Database
from app.schemas.auth import Role, UserProfile

bearer = HTTPBearer(auto_error=False, bearerFormat="JWT")
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
DUMMY_HASH = bcrypt.hashpw(b"unused", bcrypt.gensalt())


def unauthorized(message: str = "请登录后重试") -> ApiError:
    return ApiError(401, "UNAUTHORIZED", message, headers={"WWW-Authenticate": "Bearer"})


async def verify_password(password: str, encoded_hash: str | None) -> bool:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        return False
    try:
        matched = await run_in_threadpool(
            bcrypt.checkpw, raw, encoded_hash.encode("ascii") if encoded_hash else DUMMY_HASH,
        )
    except ValueError:
        await run_in_threadpool(bcrypt.checkpw, raw, DUMMY_HASH)
        return False
    return matched and encoded_hash is not None


def sign_token(user_id: int, role: Role, settings: Settings) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    return jwt.encode(
        {"sub": str(user_id), "role": role, "iat": now, "exp": now + 43200},
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


async def get_current_user(request: Request, credentials: BearerCredentials, db: Database) -> UserProfile:
    if credentials is None:
        raise unauthorized()
    try:
        claims = jwt.decode(
            credentials.credentials, request.app.state.settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"], options={"require": ["exp", "sub", "role"]},
        )
        user_id = int(claims["sub"])
        if not 0 < user_id < 2**63 or claims["role"] not in ("student", "admin"):
            raise ValueError("Invalid user claims")
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise unauthorized() from exc
    row = (
        await db.execute(
            text("SELECT id, student_no, name, role, major FROM users WHERE id = :id"),
            {"id": user_id},
        )
    ).mappings().one_or_none()
    if row is None or row["role"] != claims["role"]:
        raise unauthorized()
    return UserProfile.model_validate(row)


CurrentUser = Annotated[UserProfile, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> UserProfile:
    if user.role != "admin":
        raise ApiError(403, "FORBIDDEN", "需要管理员权限")
    return user


async def require_student(user: CurrentUser) -> UserProfile:
    if user.role != "student":
        raise ApiError(403, "FORBIDDEN", "需要学生权限")
    return user


async def require_student_write(request: Request, user: Annotated[UserProfile, Depends(require_student)]):
    await request.app.state.student_write_limiter.require(str(user.id))
    return user


Student = Annotated[UserProfile, Depends(require_student)]
Admin = Annotated[UserProfile, Depends(require_admin)]
StudentWriter = Annotated[UserProfile, Depends(require_student_write)]
