from datetime import datetime
from pathlib import Path
import sqlite3

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base


def _sqlite_path(url: str) -> Path | None:
    if not url.startswith("sqlite"):
        return None
    marker = ":///"
    if marker not in url:
        return None
    raw = url.split(marker, 1)[1]
    if not raw.startswith("/"):
        raw = "/" + raw
    return Path(raw)


def _normalize_sqlite_path(url: str) -> None:
    path = _sqlite_path(url)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)


def _backup_sqlite(url: str) -> None:
    path = _sqlite_path(url)
    if path is None or not path.exists():
        return
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"{path.stem}_{stamp}.sqlite"
    source = sqlite3.connect(path)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    backups = sorted(backup_dir.glob(f"{path.stem}_*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[7:]:
        try:
            old.unlink()
        except OSError:
            pass


settings = get_settings()
_normalize_sqlite_path(settings.database_url)
engine = create_async_engine(settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    _backup_sqlite(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            columns = await conn.execute(text("PRAGMA table_info(orders)"))
            names = {row[1] for row in columns.fetchall()}
            if "price_snapshot_toman" not in names:
                await conn.execute(text("ALTER TABLE orders ADD COLUMN price_snapshot_toman INTEGER"))
                await conn.execute(text(
                    "UPDATE orders SET price_snapshot_toman = "
                    "(SELECT price_toman FROM services WHERE services.id = orders.service_id) "
                    "WHERE price_snapshot_toman IS NULL"
                ))
