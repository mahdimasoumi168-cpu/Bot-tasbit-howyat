from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base


def _normalize_sqlite_path(url: str) -> None:
    if url.startswith("sqlite"):
        Path("data").mkdir(parents=True, exist_ok=True)


settings = get_settings()
_normalize_sqlite_path(settings.database_url)
engine = create_async_engine(settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
