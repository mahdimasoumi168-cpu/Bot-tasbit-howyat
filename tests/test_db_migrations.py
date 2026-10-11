from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.session import _ensure_sqlite_columns


async def test_legacy_sqlite_tables_receive_new_columns(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'legacy.db'}")
    async with engine.begin() as connection:
        await connection.execute(text(
            "CREATE TABLE operators (id INTEGER PRIMARY KEY, telegram_id BIGINT, created_at DATETIME)"
        ))
        await connection.execute(text(
            "INSERT INTO operators (id, telegram_id) VALUES (1, 123456789)"
        ))
        await connection.execute(text(
            "CREATE TABLE wallet_topups (id INTEGER PRIMARY KEY, amount_toman INTEGER, status VARCHAR(32))"
        ))
        await connection.execute(text(
            "CREATE TABLE discount_codes (id INTEGER PRIMARY KEY, code VARCHAR(64), value INTEGER)"
        ))
        await connection.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, telegram_id BIGINT)"
        ))
        await connection.execute(text(
            "INSERT INTO users (id, telegram_id) VALUES (1, 987654321)"
        ))

        await _ensure_sqlite_columns(connection)

        operator_columns = {
            row[1] for row in (await connection.execute(text("PRAGMA table_info(operators)"))).fetchall()
        }
        topup_columns = {
            row[1] for row in (await connection.execute(text("PRAGMA table_info(wallet_topups)"))).fetchall()
        }
        coupon_columns = {
            row[1] for row in (await connection.execute(text("PRAGMA table_info(discount_codes)"))).fetchall()
        }
        user_updated_at = (await connection.execute(
            text("SELECT updated_at FROM users WHERE id = 1")
        )).scalar_one()

        assert {"role", "permissions_json", "active", "updated_at"} <= operator_columns
        assert {"receipt_type", "reviewed_at"} <= topup_columns
        assert {"kind", "active", "max_uses", "used_count", "expires_at"} <= coupon_columns
        assert user_updated_at is not None

        operator = (await connection.execute(
            text("SELECT role, permissions_json, active, updated_at FROM operators WHERE id = 1")
        )).one()
        assert operator.role == "operator"
        assert operator.permissions_json == "{}"
        assert operator.active == 1
        assert operator.updated_at is not None

    await engine.dispose()
