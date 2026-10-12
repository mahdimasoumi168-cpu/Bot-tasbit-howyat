import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import (
    Order,
    Payment,
    Service,
    User,
    VarizaPayment,
    Wallet,
    WalletTopup,
    WalletTransaction,
)
import app.payments.variza as variza


def signed(body: bytes, secret: str = "test-secret") -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_variza_webhook_signature_verification():
    body = b'{"event":"payment.paid","status":"paid"}'
    assert variza.verify_webhook_signature(body, signed(body), "test-secret")
    assert not variza.verify_webhook_signature(body, "sha256=wrong", "test-secret")
    assert not variza.verify_webhook_signature(body, signed(body), "")


@pytest.mark.asyncio
async def test_variza_order_webhook_approves_order_once(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'variza-order.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    monkeypatch.setattr(variza, "SessionLocal", factory)
    monkeypatch.setattr(variza, "get_settings", lambda: SimpleNamespace(variza_webhook_secret="test-secret"))

    async with factory() as session:
        user = User(telegram_id=123456, first_name="Test")
        service = Service(code="identity", name="تثبیت هویت", price_toman=5000, enabled=True)
        session.add_all([user, service])
        await session.flush()
        order = Order(
            public_id="NY-1001",
            user_id=user.id,
            service_id=service.id,
            price_snapshot_toman=5000,
            status="waiting_payment",
            data_json="{}",
        )
        session.add(order)
        await session.flush()
        session.add(
            VarizaPayment(
                slug="test-order-slug",
                kind="order",
                order_id=order.id,
                user_id=user.id,
                amount_toman=5000,
                pay_url="https://variza.ir/pay/test-order-slug",
                status="pending",
            )
        )
        await session.commit()
        order_id = order.id

    body = json.dumps({
        "event": "payment.paid",
        "slug": "test-order-slug",
        "attempt_code": "attempt-1001",
        "amount": 5010,
        "base_amount": 5000,
        "status": "paid",
    }).encode()
    status, result = await variza.process_webhook(body, signed(body))
    assert status == 200
    assert result["action"] == "paid_order"

    status2, result2 = await variza.process_webhook(body, signed(body))
    assert status2 == 200
    assert result2["action"] == "duplicate"

    async with factory() as session:
        order = await session.get(Order, order_id)
        payments = (await session.execute(select(Payment).where(Payment.order_id == order_id))).scalars().all()
        record = (await session.execute(select(VarizaPayment).where(VarizaPayment.slug == "test-order-slug"))).scalar_one()
        assert order.status == "payment_approved"
        assert len(payments) == 1
        assert payments[0].status == "approved"
        assert record.status == "paid"
    await engine.dispose()


@pytest.mark.asyncio
async def test_variza_topup_webhook_adds_credit_once(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'variza-topup.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    monkeypatch.setattr(variza, "SessionLocal", factory)
    monkeypatch.setattr(variza, "get_settings", lambda: SimpleNamespace(variza_webhook_secret="test-secret"))

    async with factory() as session:
        user = User(telegram_id=654321, first_name="Test")
        session.add(user)
        await session.flush()
        wallet = Wallet(user_id=user.id, balance_toman=1500)
        topup = WalletTopup(user_id=user.id, amount_toman=25000, status="awaiting_receipt")
        session.add_all([wallet, topup])
        await session.flush()
        session.add(
            VarizaPayment(
                slug="test-topup-slug",
                kind="topup",
                topup_id=topup.id,
                user_id=user.id,
                amount_toman=25000,
                pay_url="https://variza.ir/pay/test-topup-slug",
                status="pending",
            )
        )
        await session.commit()
        topup_id = topup.id
        user_id = user.id

    body = json.dumps({
        "event": "payment.paid",
        "slug": "test-topup-slug",
        "attempt_code": "attempt-topup-1",
        "amount": 25020,
        "base_amount": 25000,
        "status": "paid",
    }).encode()
    status, result = await variza.process_webhook(body, signed(body))
    assert status == 200
    assert result["action"] == "paid_topup"
    assert result["new_balance_toman"] == 26500

    status2, result2 = await variza.process_webhook(body, signed(body))
    assert status2 == 200
    assert result2["action"] == "duplicate"

    async with factory() as session:
        wallet = (await session.execute(select(Wallet).where(Wallet.user_id == user_id))).scalar_one()
        topup = await session.get(WalletTopup, topup_id)
        transactions = (await session.execute(select(WalletTransaction).where(WalletTransaction.topup_id == topup_id))).scalars().all()
        assert wallet.balance_toman == 26500
        assert topup.status == "approved"
        assert len(transactions) == 1
    await engine.dispose()
