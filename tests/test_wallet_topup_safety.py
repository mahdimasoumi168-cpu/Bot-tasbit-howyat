from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import User, WalletTopup


async def test_wallet_topup_cannot_enter_review_queue_without_receipt(tmp_path):
    database = tmp_path / "wallet-topup-test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        user = User(telegram_id=123456789, first_name="Test")
        session.add(user)
        await session.flush()

        topup = WalletTopup(user_id=user.id, amount_toman=50_000)
        session.add(topup)
        await session.flush()
        assert topup.status == "awaiting_receipt"
        assert topup.receipt_file_id is None

        review_queue = (await session.execute(
            select(WalletTopup).where(
                WalletTopup.status == "waiting_receipt_review",
                WalletTopup.receipt_file_id.is_not(None),
            )
        )).scalars().all()
        assert review_queue == []

        topup.receipt_file_id = "test-receipt-file-id"
        topup.status = "waiting_receipt_review"
        await session.commit()

        review_queue = (await session.execute(
            select(WalletTopup).where(
                WalletTopup.status == "waiting_receipt_review",
                WalletTopup.receipt_file_id.is_not(None),
            )
        )).scalars().all()
        assert [row.id for row in review_queue] == [topup.id]

    await engine.dispose()
