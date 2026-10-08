from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ServiceCode(StrEnum):
    IDENTITY = "identity"
    KHODNEVIS = "khodnevis"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    WAITING_PAYMENT = "waiting_payment"
    WAITING_RECEIPT_REVIEW = "waiting_receipt_review"
    PAYMENT_APPROVED = "payment_approved"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    price_toman: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str | None] = mapped_column(Text)

    orders: Mapped[list["Order"]] = relationship(back_populates="service")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    price_snapshot_toman: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.DRAFT.value, index=True)
    data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    service: Mapped["Service"] = relationship(back_populates="orders")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")
    documents: Mapped[list["Document"]] = relationship(back_populates="order")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    amount_toman: Mapped[int] = mapped_column(Integer)
    receipt_file_id: Mapped[str | None] = mapped_column(String(512))
    receipt_type: Mapped[str] = mapped_column(String(16), default="photo")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="payments")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(64))
    telegram_file_id: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="documents")


class Ticket(Base):
    __tablename__="tickets"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    order_id: Mapped[int]=mapped_column(ForeignKey("orders.id"),unique=True,index=True)
    status: Mapped[str]=mapped_column(String(32),default="open",index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    updated_at: Mapped[datetime]=mapped_column(DateTime,server_default=func.now(),onupdate=func.now())
    order: Mapped["Order"]=relationship()
    messages: Mapped[list["TicketMessage"]]=relationship(back_populates="ticket",cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__="ticket_messages"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    ticket_id: Mapped[int]=mapped_column(ForeignKey("tickets.id"),index=True)
    sender_type: Mapped[str]=mapped_column(String(16))
    sender_telegram_id: Mapped[int]=mapped_column(BigInteger)
    content_type: Mapped[str]=mapped_column(String(32))
    text: Mapped[str|None]=mapped_column(Text)
    file_id: Mapped[str|None]=mapped_column(String(512))
    created_at: Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    ticket: Mapped["Ticket"]=relationship(back_populates="messages")

class Setting(Base):
    __tablename__="settings"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    key: Mapped[str]=mapped_column(String(128),unique=True,index=True)
    value: Mapped[str]=mapped_column(Text,default="")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_telegram_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), index=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class Companion(Base):
    __tablename__ = "companions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(256))
    mobile: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32), default="operator", index=True)
    permissions_json: Mapped[str] = mapped_column(Text, default="{}")
    active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
