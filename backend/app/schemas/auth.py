from typing import Literal

from pydantic import BaseModel, Field, SecretStr

Role = Literal["student", "admin"]


class LoginRequest(BaseModel):
    student_no: str = Field(min_length=1, max_length=20)
    password: SecretStr = Field(min_length=1, max_length=72)


class UserPublic(BaseModel):
    id: int
    student_no: str
    name: str
    role: Role


class UserProfile(UserPublic):
    major: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserPublic
