from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    database_url: SecretStr
    database_isolation: Literal[
        "READ_COMMITTED", "REPEATABLE_READ", "SERIALIZABLE"
    ] = "READ_COMMITTED"
    jwt_secret: SecretStr
    env: str = "dev"
    redis_url: SecretStr | None = None
    department_names: dict[int, str] = {
        1: "计算机",
        2: "软件工程",
        3: "数学",
        4: "物理",
        5: "电子",
    }

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, secret: SecretStr) -> SecretStr:
        if len(secret.get_secret_value().encode()) < 32:
            raise ValueError("JWT_SECRET must be at least 32 bytes")
        return secret
