from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from app.core.errors import error_responses
from app.core.redis import limit_login
from app.core.security import CurrentUser, sign_token, unauthorized, verify_password
from app.db.session import Database
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", dependencies=[Depends(limit_login)], responses=error_responses(429))
async def login(body: LoginRequest, request: Request, db: Database) -> LoginResponse:
    row = (
        await db.execute(
            text("SELECT id, student_no, name, role, password_hash FROM users WHERE student_no = :number"),
            {"number": body.student_no},
        )
    ).mappings().one_or_none()
    password_hash = row["password_hash"] if row else None
    await db.rollback()
    if not await verify_password(body.password.get_secret_value(), password_hash):
        raise unauthorized("账号或密码错误")
    user = UserPublic.model_validate(row)
    return LoginResponse(
        access_token=sign_token(user.id, user.role, request.app.state.settings),
        expires_in=43200,
        user=user,
    )


@router.get("/me")
async def read_profile(user: CurrentUser) -> UserProfile:
    return user
