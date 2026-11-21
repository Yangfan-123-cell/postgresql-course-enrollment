from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends, Request
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.errors import ApiError


def create_database(settings: Settings):
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        isolation_level=settings.database_isolation.replace("_", " "),
        pool_pre_ping=True,
    )
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessions() as session:
        try:
            yield session
        except (OSError, asyncpg.PostgresConnectionError, PoolTimeout) as exc:
            raise ApiError(503, "DB_UNAVAILABLE", "数据库暂不可用") from exc


Database = Annotated[AsyncSession, Depends(get_session)]
