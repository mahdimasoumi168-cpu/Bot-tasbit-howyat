from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.admin import admin_menu
from app.db.base import Base
from app.db.models import Order, Payment, Service, User
from app.db.queries import (
    find_custom_service_order_without_payment,
    list_unpriced_custom_service_orders,
)


async def test_custom_service_quote_queue_and_payment_gate(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'quotes.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        user = User(telegram_id=987654321, first_name="Test")
        service = Service(
            code="other_service",
            name="درخواست خدمات دیگر",
            price_toman=100,
            enabled=True,
        )
        session.add_all([user, service])
        await session.flush()
        order = Order(
            public_id="#Q10001",
            user_id=user.id,
            service_id=service.id,
            status="waiting_user",
            price_snapshot_toman=100,
            data_json='{"requested_service":"خدمت نمونه"}',
        )
        session.add(order)
        await session.flush()

        queue = await list_unpriced_custom_service_orders(session)
        assert [row[0].id for row in queue] == [order.id]

        found = await find_custom_service_order_without_payment(
            session,
            order.id,
            status="waiting_user",
            telegram_id=user.telegram_id,
        )
        assert found is not None
        assert found[0].public_id == "#Q10001"

        wrong_owner = await find_custom_service_order_without_payment(
            session,
            order.id,
            status="waiting_user",
            telegram_id=111111111,
        )
        assert wrong_owner is None

        order.status = "waiting_payment"
        order.price_snapshot_toman = None
        no_price = await find_custom_service_order_without_payment(
            session,
            order.id,
            status="waiting_payment",
            telegram_id=user.telegram_id,
            require_price=True,
        )
        assert no_price is None

        order.price_snapshot_toman = 250_000
        payable = await find_custom_service_order_without_payment(
            session,
            order.id,
            status="waiting_payment",
            telegram_id=user.telegram_id,
            require_price=True,
        )
        assert payable is not None
        assert payable[0].price_snapshot_toman == 250_000

        session.add(Payment(
            order_id=order.id,
            amount_toman=250_000,
            receipt_file_id="receipt-file-id",
            status="pending",
        ))
        await session.flush()

        blocked = await find_custom_service_order_without_payment(
            session,
            order.id,
            status="waiting_payment",
            telegram_id=user.telegram_id,
            require_price=True,
        )
        assert blocked is None
        assert await list_unpriced_custom_service_orders(session) == []

    await engine.dispose()


def test_admin_menu_exposes_custom_service_quote_queue():
    callbacks = {
        button.callback_data
        for row in admin_menu().inline_keyboard
        for button in row
    }
    assert "adm:unpriced" in callbacks
