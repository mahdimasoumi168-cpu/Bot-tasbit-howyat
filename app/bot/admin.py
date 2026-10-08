import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove
from sqlalchemy import select

from app.bot.handlers import STATUS_TEXT
from app.bot.states import AdminForm
from app.core.config import get_settings
from app.db.models import Companion, Document, Order, Payment, Service, Setting, Ticket, TicketMessage, User
from app.db.session import SessionLocal

router = Router()


def is_admin(message: Message) -> bool:
    return message.from_user.id in get_settings().admin_id_set


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔵 رسیدهای در انتظار بررسی", callback_data="adm:pending")],
            [InlineKeyboardButton(text="📋 آخرین درخواست‌ها", callback_data="adm:orders")],
            [InlineKeyboardButton(text="💳 تنظیم کارت", callback_data="adm:setcard")],
            [InlineKeyboardButton(text="💰 تنظیم قیمت‌ها", callback_data="adm:prices")],
        ]
    )


def order_actions(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"adm:approve:{order_id}")],
            [InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"adm:reject:{order_id}")],
            [InlineKeyboardButton(text="💬 پیام به مشترک", callback_data=f"adm:msg:{order_id}")],
        ]
    )


def status_header(order: Order, service: Service) -> str:
    return f"{order.public_id} | {STATUS_TEXT.get(order.status, order.status)}\n🪪 خدمت: {service.name}"


@router.message(F.text == "/admin")
async def admin_start(message: Message) -> None:
    if not is_admin(message):
        return
    await message.answer("🛠 پنل مدیریت", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:setcard")
async def set_card_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.set_state(AdminForm.set_card)
    await callback.answer()
    await callback.message.answer(
        "شماره کارت و نام صاحب کارت را در یک پیام و با | جدا کنید.\n"
        "مثال: 6037991234567890 | نام صاحب کارت"
    )


@router.message(AdminForm.set_card)
async def set_card_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    parts = [x.strip() for x in (message.text or "").split("|", 1)]
    if len(parts) != 2 or not parts[0].isdigit() or len(parts[0]) != 16 or not parts[1]:
        await message.answer("❌ قالب صحیح نیست. دوباره بفرستید: شماره کارت | نام صاحب کارت")
        return
    async with SessionLocal() as session:
        for key, value in (("card_number", parts[0]), ("card_holder", parts[1])):
            row = (
                await session.execute(select(Setting).where(Setting.key == key))
            ).scalar_one_or_none()
            if row is None:
                session.add(Setting(key=key, value=value))
            else:
                row.value = value
        await session.commit()
    await state.clear()
    await message.answer("✅ اطلاعات کارت ذخیره شد.", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:prices")
async def prices(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        rows = (await session.execute(select(Service).order_by(Service.id))).scalars().all()
    text = "💰 قیمت فعلی خدمات:\n\n" + "\n".join(
        f"{s.name}: {s.price_toman:,} تومان" for s in rows
    ) or "خدمتی ثبت نشده است."
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🪪 تغییر قیمت تثبیت هویت", callback_data="adm:setprice:identity")],
            [InlineKeyboardButton(text="📝 تغییر قیمت کد رهگیری خودنویس", callback_data="adm:setprice:khodnevis")],
            [InlineKeyboardButton(text="🔙 بازگشت به پنل", callback_data="adm:home")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "adm:home")
async def admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await callback.message.edit_text("🛠 پنل مدیریت\n\nاز گزینه‌های زیر استفاده کنید:", reply_markup=admin_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("adm:setprice:"))
async def set_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    service_code = callback.data.rsplit(":", 1)[1]
    if service_code not in {"identity", "khodnevis"}:
        await callback.answer("خدمت نامعتبر است.", show_alert=True)
        return
    await state.clear()
    await state.update_data(price_service=service_code)
    await state.set_state(AdminForm.set_price)
    await callback.answer()
    await callback.message.answer(
        "💰 مبلغ جدید را فقط به تومان و به صورت عددی ارسال کنید.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminForm.set_price)
async def set_price_from_panel(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = (message.text or "").replace(",", "").replace("٬", "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("❌ مبلغ نامعتبر است. فقط عدد مثبت را ارسال کنید.")
        return
    data = await state.get_data()
    service_code = data.get("price_service")
    if service_code not in {"identity", "khodnevis"}:
        await state.clear()
        await message.answer("❌ خدمت مشخص نیست.", reply_markup=admin_menu())
        return
    async with SessionLocal() as session:
        service = (await session.execute(select(Service).where(Service.code == service_code))).scalar_one_or_none()
        if service is None:
            await state.clear()
            await message.answer("❌ خدمت پیدا نشد.", reply_markup=admin_menu())
            return
        service.price_toman = int(raw)
        name = service.name
        await session.commit()
    await state.clear()
    await message.answer(f"✅ قیمت «{name}» به {int(raw):,} تومان تغییر کرد.", reply_markup=admin_menu())


@router.message(F.text.startswith("/setprice"))
async def set_price(message: Message) -> None:
    if not is_admin(message):
        return
    parts = (message.text or "").split()
    if len(parts) != 3 or parts[1] not in {"identity", "khodnevis"} or not parts[2].isdigit():
        await message.answer("فرمت: /setprice identity 280000")
        return
    price = int(parts[2])
    if price <= 0:
        await message.answer("❌ مبلغ باید بیشتر از صفر باشد.")
        return
    async with SessionLocal() as session:
        service = (
            await session.execute(select(Service).where(Service.code == parts[1]))
        ).scalar_one_or_none()
        if service is None:
            await message.answer("❌ خدمت پیدا نشد.")
            return
        service.price_toman = price
        await session.commit()
    await message.answer("✅ قیمت ذخیره شد.", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:pending")
async def pending(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        result = await session.execute(
            select(Payment, Order, Service, User)
            .join(Order, Payment.order_id == Order.id)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(Payment.status == "pending")
            .order_by(Payment.id.desc())
            .limit(20)
        )
        rows = result.all()
    if not rows:
        await callback.message.edit_text("رسید در انتظار بررسی وجود ندارد.", reply_markup=admin_menu())
        await callback.answer()
        return
    await callback.message.edit_text("🔵 رسیدهای در انتظار بررسی:")
    for payment, order, service, user in rows:
        await callback.message.answer(
            f"{status_header(order, service)}\n"
            f"👤 مشترک: {user.first_name or ''} {user.last_name or ''}\n"
            f"📱 شناسه تلگرام: {user.telegram_id}\n"
            f"💰 مبلغ: {payment.amount_toman:,} تومان",
            reply_markup=order_actions(order.id),
        )
        if payment.receipt_file_id:
            await callback.message.answer_photo(
                payment.receipt_file_id, caption=f"🧾 رسید {order.public_id}"
            )
    await callback.answer()


@router.callback_query(F.data == "adm:orders")
async def orders(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        result = await session.execute(
            select(Order, Service, User)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .order_by(Order.id.desc())
            .limit(20)
        )
        rows = result.all()
    text = "📋 آخرین درخواست‌ها:\n\n"
    text += "\n".join(
        f"{o.public_id} | {STATUS_TEXT.get(o.status, o.status)} | {s.name} | {u.telegram_id}"
        for o, s, u in rows
    )
    await callback.message.edit_text(text or "درخواستی ثبت نشده است.", reply_markup=admin_menu())
    await callback.answer()


async def send_case_to_operator(bot, order_id: int) -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Order, Service, User)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(Order.id == order_id)
            )
        ).one_or_none()
        if not row:
            return
        order, service, user = row
        docs = (
            await session.execute(
                select(Document).where(Document.order_id == order.id).order_by(Document.id)
            )
        ).scalars().all()
        companions = (
            await session.execute(
                select(Companion).where(Companion.order_id == order.id).order_by(Companion.id)
            )
        ).scalars().all()
        payment = (
            await session.execute(
                select(Payment)
                .where(Payment.order_id == order.id)
                .order_by(Payment.id.desc())
            )
        ).scalars().first()
        data = json.loads(order.data_json or "{}")

    text = (
        f"{status_header(order, service)}\n"
        f"👤 مشترک: {data.get('full_name', '')}\n"
        f"📱 موبایل در دسترس: {data.get('mobile', '')}\n"
        f"🆔 شناسه تلگرام: {user.telegram_id}\n"
    )
    if service.code == "identity":
        text += (
            f"🎂 تاریخ تولد: {data.get('birth_date_gregorian', '')}\n"
            f"✈️ آخرین تاریخ بازگشت به افغانستان: {data.get('return_date_gregorian', '')}\n"
            f"🇦🇫 کنسولگری: {data.get('consulate', '')}\n"
            f"👥 همراهان: {'ندارد' if not companions else 'دارد'}\n"
        )
        if companions:
            text += "\n".join(f"• {x.full_name} — {x.mobile}" for x in companions)
    else:
        text += (
            f"🪪 مدرک: {data.get('document_type', '')}\n"
            f"📱 موبایل به نام شخص: {data.get('own_mobile', '')}\n"
        )

    for admin_id in settings.admin_id_set:
        await bot.send_message(admin_id, text, reply_markup=order_actions(order.id))
        if payment and payment.receipt_file_id:
            await bot.send_photo(
                admin_id, payment.receipt_file_id, caption=f"🧾 رسید پرداخت {order.public_id}"
            )
        for doc in docs:
            await bot.send_photo(
                admin_id, doc.telegram_file_id, caption=f"📎 {doc.document_type} | {order.public_id}"
            )


@router.callback_query(F.data.startswith("adm:approve:"))
async def approve(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        payment = (
            await session.execute(
                select(Payment)
                .where(Payment.order_id == order_id, Payment.status == "pending")
                .order_by(Payment.id.desc())
            )
        ).scalars().first()
        if not order or not payment:
            await callback.answer("درخواست یا رسید در انتظار بررسی پیدا نشد.", show_alert=True)
            return
        payment.status = "approved"
        order.status = "payment_approved"
        ticket = (
            await session.execute(select(Ticket).where(Ticket.order_id == order_id))
        ).scalar_one_or_none()
        if ticket is None:
            session.add(Ticket(order_id=order_id, status="open"))
        await session.commit()
        user = await session.get(User, order.user_id)
    await callback.answer("پرداخت تأیید شد.")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.bot.send_message(
        user.telegram_id,
        f"✅ پرداخت درخواست {order.public_id} تأیید شد.\nدرخواست شما وارد مرحله انجام شد.",
    )
    await send_case_to_operator(callback.bot, order_id)


@router.callback_query(F.data.startswith("adm:reject:"))
async def reject(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        payment = (
            await session.execute(
                select(Payment)
                .where(Payment.order_id == order_id, Payment.status == "pending")
                .order_by(Payment.id.desc())
            )
        ).scalars().first()
        if not order or not payment:
            await callback.answer("رسید پیدا نشد.", show_alert=True)
            return
        payment.status = "rejected"
        order.status = "rejected"
        user = await session.get(User, order.user_id)
        await session.commit()
    await callback.answer("رسید رد شد.")
    await callback.message.edit_reply_markup(reply_markup=None)
    retry_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧾 ارسال مجدد رسید", callback_data=f"retry_receipt:{order.id}")]
        ]
    )
    await callback.message.bot.send_message(
        user.telegram_id,
        f"❌ رسید درخواست {order.public_id} تأیید نشد.\n"
        "می‌توانید رسید صحیح را همین حالا دوباره ارسال کنید.",
        reply_markup=retry_keyboard,
    )


@router.callback_query(F.data.startswith("adm:msg:"))
async def start_message(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    await state.update_data(admin_order_id=order_id)
    await state.set_state(AdminForm.send_message)
    await callback.answer()
    await callback.message.answer("💬 پیام خود را ارسال کنید. متن، عکس، فایل، ویدیو یا صوت قابل ارسال است.")


@router.message(AdminForm.send_message)
async def send_message_to_user(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    data = await state.get_data()
    order_id = data.get("admin_order_id")
    if not order_id:
        await state.clear()
        return
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Order, Service, User)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(Order.id == order_id)
            )
        ).one_or_none()
        ticket = (
            await session.execute(select(Ticket).where(Ticket.order_id == order_id))
        ).scalar_one_or_none()
        if not row or not ticket:
            await state.clear()
            await message.answer("❌ تیکت فعال پیدا نشد.")
            return
        order, service, user = row
        session.add(
            TicketMessage(
                ticket_id=ticket.id,
                sender_type="admin",
                sender_telegram_id=message.from_user.id,
                content_type=message.content_type,
                text=message.text or message.caption,
            )
        )
        await session.commit()
    await message.bot.send_message(user.telegram_id, status_header(order, service))
    await message.copy_to(user.telegram_id)
    await state.clear()
    await message.answer("✅ پیام ارسال شد.", reply_markup=admin_menu())


@router.message()
async def user_ticket_reply(message: Message) -> None:
    if message.from_user.id in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Ticket, Order, Service)
                .join(Order, Ticket.order_id == Order.id)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(
                    User.telegram_id == message.from_user.id,
                    Ticket.status == "open",
                )
                .order_by(Ticket.id.desc())
            )
        ).first()
        if not row:
            return
        ticket, order, service = row
        session.add(
            TicketMessage(
                ticket_id=ticket.id,
                sender_type="user",
                sender_telegram_id=message.from_user.id,
                content_type=message.content_type,
                text=message.text or message.caption,
            )
        )
        await session.commit()
    for admin_id in get_settings().admin_id_set:
        await message.bot.send_message(
            admin_id, status_header(order, service) + f"\n👤 پاسخ مشترک: {message.from_user.id}"
        )
        await message.copy_to(admin_id)
