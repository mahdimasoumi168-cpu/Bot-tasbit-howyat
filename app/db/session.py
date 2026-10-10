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
            wallet_columns = await conn.execute(text("PRAGMA table_info(wallets)"))
            wallet_names = {row[1] for row in wallet_columns.fetchall()}
            if not wallet_names:
                await conn.execute(text("CREATE TABLE IF NOT EXISTS wallets (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL, balance_toman INTEGER NOT NULL DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            await conn.execute(text("CREATE TABLE IF NOT EXISTS wallet_topups (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, amount_toman INTEGER NOT NULL, receipt_file_id VARCHAR(512), receipt_type VARCHAR(16) DEFAULT 'photo', status VARCHAR(32) DEFAULT 'waiting_receipt_review', created_at DATETIME DEFAULT CURRENT_TIMESTAMP, reviewed_at DATETIME)"))
            await conn.execute(text("CREATE TABLE IF NOT EXISTS wallet_transactions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, amount_toman INTEGER NOT NULL, balance_after_toman INTEGER NOT NULL, kind VARCHAR(32) NOT NULL, description VARCHAR(512) NOT NULL, order_id INTEGER, topup_id INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            await conn.execute(text("CREATE TABLE IF NOT EXISTS discount_codes (id INTEGER PRIMARY KEY, code VARCHAR(64) UNIQUE NOT NULL, kind VARCHAR(16) DEFAULT 'percent', value INTEGER NOT NULL, active BOOLEAN DEFAULT 1, max_uses INTEGER, used_count INTEGER DEFAULT 0, expires_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            payment_columns = await conn.execute(text("PRAGMA table_info(payments)"))
            payment_names = {row[1] for row in payment_columns.fetchall()}
            if "receipt_type" not in payment_names:
                await conn.execute(text("ALTER TABLE payments ADD COLUMN receipt_type VARCHAR(16) DEFAULT 'photo'"))
                await conn.execute(text("UPDATE payments SET receipt_type = 'photo' WHERE receipt_type IS NULL"))
            document_columns = await conn.execute(text("PRAGMA table_info(documents)"))
            document_names = {row[1] for row in document_columns.fetchall()}
            if "review_status" not in document_names:
                await conn.execute(text(
                    "ALTER TABLE documents ADD COLUMN review_status VARCHAR(32) NOT NULL DEFAULT 'pending'"
                ))
            if "reviewed_by_telegram_id" not in document_names:
                await conn.execute(text(
                    "ALTER TABLE documents ADD COLUMN reviewed_by_telegram_id BIGINT"
                ))
            if "reviewed_at" not in document_names:
                await conn.execute(text(
                    "ALTER TABLE documents ADD COLUMN reviewed_at DATETIME"
                ))
