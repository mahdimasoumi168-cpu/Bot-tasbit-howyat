from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, Payment, Service, User


async def list_unpriced_custom_service_orders(session: AsyncSession, limit: int = 30):
    """Return custom-service inquiries awaiting a quote and with no payment record."""
    result = await session.execute(
        select(Order, Service, User)
        .join(Service, Service.id == Order.service_id)
        .join(User, User.id == Order.user_id)
        .outerjoin(Payment, Payment.order_id == Order.id)
        .where(
            Service.code == "other_service",
            Order.status == "waiting_user",
            Payment.id.is_(None),
        )
        .order_by(Order.created_at.asc())
        .limit(limit)
    )
    return result.all()


async def find_custom_service_order_without_payment(
    session: AsyncSession,
    order_id: int,
    *,
    status: str,
    telegram_id: int | None = None,
    require_price: bool = False,
):
    """Load a custom-service order only when it is in the expected state and unpaid."""
    query = (
        select(Order, Service, User)
        .join(Service, Service.id == Order.service_id)
        .join(User, User.id == Order.user_id)
        .outerjoin(Payment, Payment.order_id == Order.id)
        .where(
            Order.id == order_id,
            Service.code == "other_service",
            Order.status == status,
            Payment.id.is_(None),
        )
    )
    if telegram_id is not None:
        query = query.where(User.telegram_id == telegram_id)
    if require_price:
        query = query.where(
            Order.price_snapshot_toman.is_not(None),
            Order.price_snapshot_toman > 0,
        )
    result = await session.execute(query)
    return result.one_or_none()
