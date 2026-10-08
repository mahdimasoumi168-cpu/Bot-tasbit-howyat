import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove
from sqlalchemy import or_, select

from app.bot.handlers import STATUS_TEXT
from app.bot.states import AdminForm
from app.core.config import get_settings
from app.db.models import AuditLog, Companion, Document, Order, Operator, Payment, Service, Setting, Ticket, TicketMessage, User
from app.db.session import SessionLocal

router = Router()


async def audit(actor_id: int, action: str, order_id: int | None = None, details: dict | None = None) -> None:
    async with SessionLocal() as session:
        session.add(AuditLog(
            actor_telegram_id=actor_id,
            action=action,
            order_id=order_id,
            details_json=json.dumps(details or {}, ensure_ascii=False),
        ))
        await session.commit()


def is_admin(message: Message) -> bool:
    return message.from_user.id in get_settings().admin_id_set


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔵 رسیدهای در انتظار بررسی", callback_data="adm:pending")],
            [InlineKeyboardButton(text="📋 درخواست‌ها", callback_data="adm:orders")],
            [InlineKeyboardButton(text="🔎 پرونده با کد پیگیری", callback_data="adm:case")],
            [InlineKeyboardButton(text="📊 گزارش‌ها", callback_data="adm:stats")],
            [InlineKeyboardButton(text="👥 مشترکان", callback_data="adm:users")],
            [InlineKeyboardButton(text="👨‍💼 اپراتورها", callback_data="adm:operators")],
            [InlineKeyboardButton(text="🧩 خدمات", callback_data="adm:services")],
            [InlineKeyboardButton(text="💰 قیمت خدمات", callback_data="adm:prices")],
            [InlineKeyboardButton(text="💳 اطلاعات کارت", callback_data="adm:card")],
            [InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="adm:settings")],
        ]
    )


def order_actions(order_id: int, operator: Operator | None = None) -> InlineKeyboardMarkup:
    rows = []
    if operator is None:
        rows.append([InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"adm:approve:{order_id}")])
        rows.append([InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"adm:reject:{order_id}")])
    else:
        if can_operator(operator, "approve_payment"):
            rows.append([InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"adm:approve:{order_id}")])
        if can_operator(operator, "reject_payment"):
            rows.append([InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"adm:reject:{order_id}")])
    if operator is None or can_operator(operator, "set_status"):
        rows.extend([
            [InlineKeyboardButton(text="🟡 در حال انجام", callback_data=f"adm:status:{order_id}:in_progress")],
            [InlineKeyboardButton(text="⏳ منتظر مشترک", callback_data=f"adm:status:{order_id}:waiting_user")],
            [InlineKeyboardButton(text="✅ تکمیل درخواست", callback_data=f"adm:status:{order_id}:completed")],
            [InlineKeyboardButton(text="🔴 رد درخواست", callback_data=f"adm:status:{order_id}:rejected")],
        ])
    if operator is None or can_operator(operator, "message_user"):
        rows.append([InlineKeyboardButton(text="💬 پیام به مشترک", callback_data=f"adm:msg:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def status_header(order: Order, service: Service) -> str:
    return f"{order.public_id} | {STATUS_TEXT.get(order.status, order.status)}\n🪪 خدمت: {service.name}"



@router.message(F.text == "👨‍💼 پنل اپراتور")
async def operator_button(message: Message, state: FSMContext) -> None:
    if message.from_user.id in get_settings().admin_id_set:
        await admin_start(message, state)
        return
    operator = await get_operator(message.from_user.id)
    if operator is None:
        return
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 درخواست‌های قابل رسیدگی", callback_data="op:orders")],
        [InlineKeyboardButton(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="op:back")],
    ])
    await message.answer("👨‍💼 پنل اپراتور\n\nدسترسی‌های شما بر اساس تنظیمات مدیریت نمایش داده می‌شود.", reply_markup=keyboard)


@router.callback_query(F.data == "op:back")
async def operator_back(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None:
        return
    await callback.message.edit_text("👨‍💼 پنل اپراتور", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 درخواست‌های قابل رسیدگی", callback_data="op:orders")],
        [InlineKeyboardButton(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
    ]))
    await callback.answer()


@router.callback_query(F.data == "op:orders")
async def operator_orders(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی مشاهده درخواست‌ها را ندارید.", show_alert=True)
        return
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(Order, Service, User)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(Order.status.in_(["payment_approved", "in_progress", "waiting_user"]))
            .order_by(Order.updated_at.desc())
            .limit(30)
        )).all()
    if not rows:
        text = "📋 درخواستی برای رسیدگی وجود ندارد."
    else:
        text = "📋 درخواست‌های قابل رسیدگی\n\n" + "\n".join(
            f"{o.public_id} | {STATUS_TEXT.get(o.status,o.status)} | {s.name}"
            for o,s,u in rows
        )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=o.public_id, callback_data=f"op:order:{o.id}")]
        for o,s,u in rows
    ] + [[InlineKeyboardButton(text="🔙 بازگشت", callback_data="op:back")]]))
    await callback.answer()


@router.callback_query(F.data.startswith("op:order:"))
async def operator_order_detail(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    order_id = int(callback.data.rsplit(":",1)[1])
    async with SessionLocal() as session:
        row = (await session.execute(
            select(Order, Service, User).join(Service, Order.service_id==Service.id).join(User, Order.user_id==User.id).where(Order.id==order_id)
        )).one_or_none()
    if not row:
        await callback.answer("درخواست پیدا نشد.", show_alert=True)
        return
    order, service, user = row
    await callback.message.edit_text(
        f"{status_header(order,service)}\n"
        f"👤 {user.first_name or ''} {user.last_name or ''}\n"
        f"🆔 {user.telegram_id}\n"
        f"💰 مبلغ ثبت‌شده: {(order.price_snapshot_toman or service.price_toman):,} تومان",
        reply_markup=order_actions(order.id, operator=operator),
    )
    await callback.answer()


@router.callback_query(F.data == "op:pending")
async def operator_pending(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    async with SessionLocal() as session:
        rows=(await session.execute(
            select(Payment,Order,Service,User)
            .join(Order,Payment.order_id==Order.id)
            .join(Service,Order.service_id==Service.id)
            .join(User,Order.user_id==User.id)
            .where(Payment.status=="pending")
            .order_by(Payment.id.desc()).limit(20)
        )).all()
    if not rows:
        await callback.message.edit_text("🔵 رسید در انتظار بررسی وجود ندارد.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت",callback_data="op:back")]
        ]))
        await callback.answer()
        return
    await callback.message.edit_text("🔵 رسیدهای در انتظار بررسی:")
    for payment, order, service, user in rows:
        await callback.message.answer(
            f"{status_header(order, service)}\n"
            f"👤 {user.first_name or ''} {user.last_name or ''}\n"
            f"💰 {payment.amount_toman:,} تومان",
            reply_markup=order_actions(order.id, operator=operator),
        )
        if payment.receipt_file_id:
            await callback.message.answer_photo(
                payment.receipt_file_id,
                caption=f"🧾 رسید {order.public_id}",
            )
    await callback.answer()


@router.callback_query(F.data == "menu:admin")
async def inline_admin_open(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.clear()
    await callback.answer()
    await callback.message.edit_text("🛠 پنل مدیریت\n\nبخش موردنظر را انتخاب کنید:", reply_markup=admin_menu())

@router.callback_query(F.data == "menu:operator")
async def inline_operator_open(callback: CallbackQuery, state: FSMContext) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None:
        await callback.answer("شما اپراتور فعال نیستید.", show_alert=True)
        return
    await state.clear()
    await callback.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 درخواست‌های قابل رسیدگی", callback_data="op:orders")],
        [InlineKeyboardButton(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="op:back")],
    ])
    await callback.message.edit_text("👨‍💼 پنل اپراتور\n\nبخش موردنظر را انتخاب کنید:", reply_markup=keyboard)


@router.message(F.text == "/admin")
async def admin_start(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    await state.clear()
    await message.answer("🛠 پنل مدیریت\n\nاز گزینه‌های زیر استفاده کنید:", reply_markup=admin_menu())


@router.message(F.text == "🛠 پنل مدیریت")
async def admin_button(message: Message, state: FSMContext) -> None:
    await admin_start(message, state)


@router.callback_query(F.data == "adm:setcard")
async def set_card_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.set_card_number)
    await callback.answer()
    await callback.message.answer(
        "💳 مرحله ۱ از ۲\nشماره کارت ۱۶ رقمی را فقط به صورت عددی ارسال کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminForm.set_card_number)
async def set_card_number_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    value = (message.text or "").replace(" ", "").replace("-", "").strip()
    if not value.isdigit() or len(value) != 16:
        await message.answer("❌ شماره کارت باید دقیقاً ۱۶ رقم باشد. دوباره وارد کنید:")
        return
    await state.update_data(card_number=value)
    await state.set_state(AdminForm.set_card_holder)
    await message.answer("💳 مرحله ۲ از ۲\nنام صاحب کارت را وارد کنید:")


@router.message(AdminForm.set_card_holder)
async def set_card_holder_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    holder = (message.text or "").strip()
    if len(holder) < 2:
        await message.answer("❌ نام صاحب کارت معتبر نیست. دوباره وارد کنید:")
        return
    data = await state.get_data()
    async with SessionLocal() as session:
        for key, value in (("card_number", data["card_number"]), ("card_holder", holder)):
            row = (await session.execute(select(Setting).where(Setting.key == key))).scalar_one_or_none()
            if row is None:
                session.add(Setting(key=key, value=value))
            else:
                row.value = value
        await session.commit()
    await state.clear()
    await message.answer("✅ اطلاعات کارت با موفقیت ذخیره شد.", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:card")
async def show_card(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        number = (await session.execute(select(Setting).where(Setting.key == "card_number"))).scalar_one_or_none()
        holder = (await session.execute(select(Setting).where(Setting.key == "card_holder"))).scalar_one_or_none()
    await callback.message.edit_text(
        "💳 اطلاعات کارت\n\n"
        f"شماره کارت: {number.value if number and number.value else 'تنظیم نشده'}\n"
        f"نام صاحب کارت: {holder.value if holder and holder.value else 'تنظیم نشده'}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ ویرایش اطلاعات کارت", callback_data="adm:setcard")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:home")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:settings")
async def settings_panel(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await callback.message.edit_text(
        "⚙️ تنظیمات مدیریت\n\n"
        "مدیریت اطلاعات حساس و تنظیمات پایه از همین پنل انجام می‌شود.\n"
        "در این بخش فعلاً اطلاعات کارت و قیمت خدمات قابل مدیریت است.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 اطلاعات کارت", callback_data="adm:card")],
            [InlineKeyboardButton(text="💰 قیمت خدمات", callback_data="adm:prices")],
            [InlineKeyboardButton(text="🧩 وضعیت خدمات", callback_data="adm:services")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:home")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:services")
async def services_panel(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        rows = (await session.execute(select(Service).order_by(Service.id))).scalars().all()
    buttons = []
    for service in rows:
        state_text = "🟢 فعال" if service.enabled else "🔴 غیرفعال"
        buttons.append([InlineKeyboardButton(
            text=f"{state_text} | {service.name}",
            callback_data=f"adm:toggle:{service.id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:home")])
    text = "🧩 مدیریت خدمات\n\nبرای فعال/غیرفعال کردن هر خدمت، روی همان خدمت بزنید."
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:toggle:"))
async def toggle_service(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with SessionLocal() as session:
        service = await session.get(Service, service_id)
        if service is None:
            await callback.answer("خدمت پیدا نشد.", show_alert=True)
            return
        service.enabled = not service.enabled
        await session.commit()
        state_text = "فعال" if service.enabled else "غیرفعال"
    await services_panel(callback)


@router.callback_query(F.data == "adm:case")
async def case_lookup_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.case_lookup)
    await callback.answer()
    await callback.message.answer(
        "🔎 مشاهده پرونده کامل\n\n"
        "کد پیگیری را وارد کنید. مثال: #10001 یا 10001",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminForm.case_lookup)
async def case_lookup(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = (message.text or "").strip().lstrip("#").strip()
    if not raw.isdigit():
        await message.answer("❌ کد پیگیری نامعتبر است. مثال: #10001")
        return
    public_id = f"#{raw}"
    async with SessionLocal() as session:
        row = (await session.execute(
            select(Order, Service, User)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(Order.public_id == public_id)
        )).one_or_none()
        if not row:
            await message.answer("❌ پرونده‌ای با این کد پیگیری پیدا نشد. دوباره وارد کنید:")
            return
        order, service, user = row
        data = json.loads(order.data_json or "{}")
        companions = (await session.execute(
            select(Companion).where(Companion.order_id == order.id).order_by(Companion.id)
        )).scalars().all()
        documents = (await session.execute(
            select(Document).where(Document.order_id == order.id).order_by(Document.id)
        )).scalars().all()
        payments = (await session.execute(
            select(Payment).where(Payment.order_id == order.id).order_by(Payment.id.desc())
        )).scalars().all()
    await state.clear()
    await message.answer(
        build_case_text(order, service, user, data, companions, documents, payments),
        reply_markup=order_actions(order.id),
    )
    for doc in documents:
        try:
            await message.answer_photo(
                doc.telegram_file_id,
                caption=f"📎 {doc.document_type} | {order.public_id}",
            )
        except Exception:
            await message.answer(f"⚠️ تصویر «{doc.document_type}» قابل ارسال مجدد نبود.")
    if not documents:
        await message.answer("📎 برای این پرونده تصویری در سیستم ثبت نشده است.")


PAYMENT_STATUS_TEXT = {\n    "pending": "در انتظار بررسی",\n    "approved": "تأیید شده",\n    "rejected": "رد شده",\n    "superseded": "جایگزین شده",\n}\n\n\ndef build_case_text(order: Order, service: Service, user: User, data: dict, companions, documents, payments) -> str:
    name = data.get("full_name") or f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"
    mobile = data.get("mobile") or "—"
    lines = [
        "📁 پرونده کامل مشترک",
        "",
        f"🔖 کد پیگیری: {order.public_id}",
        f"🧾 خدمت: {service.name}",
        f"📌 وضعیت: {STATUS_TEXT.get(order.status, order.status)}",
        f"💰 مبلغ پرونده: {(order.price_snapshot_toman or service.price_toman):,} تومان",
        f"📅 ثبت: {order.created_at.strftime('%Y/%m/%d %H:%M') if order.created_at else '—'}",
        "",
        "👤 اطلاعات شخص",
        f"نام و نام خانوادگی: {name}",
        f"📱 موبایل: {mobile}",
    ]
    skip = {"full_name", "mobile", "identity_document", "tazkira", "amayesh", "passport_first", "passport_renewal", "residence_renewal"}
    for key, value in data.items():
        if key in skip or value in (None, "", [], {}):
            continue
        label = {
            "birth_date_gregorian": "تاریخ تولد",
            "return_date_gregorian": "آخرین بازگشت به افغانستان",
            "consulate": "کنسولگری",
            "document_type": "نوع مدرک",
            "own_mobile": "موبایل به نام شخص",
        }.get(key, key.replace("_", " "))
        if isinstance(value, list):
            continue
        lines.append(f"• {label}: {value}")
    lines.append("")
    lines.append("👨‍👩‍👧 همراهان")
    lines.extend([f"• {x.full_name} — {x.mobile}" for x in companions] or ["ندارد"])
    lines.append("")
    lines.append("💳 سوابق پرداخت")
    if payments:
        for p in payments:
            lines.append(f"• {PAYMENT_STATUS_TEXT.get(p.status, 'نامشخص')} — {p.amount_toman:,} تومان — {p.created_at.strftime('%Y/%m/%d %H:%M') if p.created_at else '—'}")
    else:
        lines.append("• پرداختی ثبت نشده است")
    lines.append("")
    lines.append("📎 مدارک: " + (", ".join(d.document_type for d in documents) if documents else "ندارد"))
    return "\n".join(lines)


@router.callback_query(F.data == "adm:users")
async def users_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.user_search)
    await callback.answer()
    await callback.message.answer(
        "👥 جستجوی مشترک\n\nنام، نام کاربری، شناسه تلگرام یا شماره درخواست را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminForm.user_search)
async def user_search(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("❌ عبارت جستجو را وارد کنید.")
        return
    async with SessionLocal() as session:
        user = None
        if raw.isdigit():
            user = (await session.execute(
                select(User).where(User.telegram_id == int(raw))
            )).scalar_one_or_none()
        if user is None:
            normalized = raw.lstrip("#")
            order_match = (await session.execute(
                select(Order).where(Order.public_id == f"#{normalized}")
            )).scalar_one_or_none()
            if order_match:
                user = await session.get(User, order_match.user_id)
        if user is None:
            pattern = f"%{raw}%"
            user = (await session.execute(
                select(User).where(
                    or_(
                        User.first_name.ilike(pattern),
                        User.last_name.ilike(pattern),
                        User.username.ilike(pattern),
                    )
                ).order_by(User.id.desc()).limit(1)
            )).scalar_one_or_none()
        if user is None:
            order_match = (await session.execute(
                select(Order).where(Order.data_json.ilike(pattern)).order_by(Order.id.desc()).limit(1)
            )).scalar_one_or_none()
            if order_match:
                user = await session.get(User, order_match.user_id)
        if user is None:
            await message.answer("❌ مشترک پیدا نشد. نام، نام کاربری، شناسه تلگرام یا شماره درخواست را امتحان کنید:")
            return
        orders = (await session.execute(
            select(Order, Service).join(Service, Order.service_id == Service.id)
            .where(Order.user_id == user.id).order_by(Order.id.desc()).limit(30)
        )).all()
    text = (
        "👤 اطلاعات مشترک\n\n"
        f"شناسه تلگرام: {user.telegram_id}\n"
        f"نام: {(user.first_name or '')} {(user.last_name or '')}".strip() +
        f"\nنام کاربری: @{user.username if user.username else 'ندارد'}\n\n"
        "📋 آخرین درخواست‌ها:\n"
    )
    text += "\n".join(
        f"{o.public_id} | {STATUS_TEXT.get(o.status, o.status)} | {s.name}" for o, s in orders
    ) or "درخواستی ندارد."
    await state.clear()
    await message.answer(text, reply_markup=admin_menu())


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
        await message.answer("برای تغییر قیمت، از بخش «💰 قیمت خدمات» در پنل مدیریت استفاده کنید.")
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



@router.callback_query(F.data == "adm:stats")
async def admin_stats(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    async with SessionLocal() as session:
        total = (await session.execute(select(Order))).scalars().all()
        counts = {}
        for order in total:
            counts[order.status] = counts.get(order.status, 0) + 1
        approved = (await session.execute(
            select(Payment).where(Payment.status == "approved")
        )).scalars().all()
        revenue = sum(p.amount_toman for p in approved)
        users_count = len((await session.execute(select(User))).scalars().all())
    lines = [
        "📊 گزارش کلی رنا یار بات",
        "",
        f"👥 مشترکان: {users_count}",
        f"📋 کل درخواست‌ها: {len(total)}",
        f"🔵 رسیدهای تأییدشده: {len(approved)}",
        f"💰 مبلغ پرداخت‌های تأییدشده: {revenue:,} تومان",
        "",
    ]
    for key, label in [
        ("waiting_payment","در انتظار پرداخت"),
        ("waiting_receipt_review","در انتظار بررسی رسید"),
        ("payment_approved","پرداخت تأیید شده"),
        ("in_progress","در حال انجام"),
        ("waiting_user","منتظر مشترک"),
        ("completed","تکمیل شده"),
        ("rejected","رد شده"),
    ]:
        lines.append(f"{label}: {counts.get(key,0)}")
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:home")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:order:"))
async def admin_order_detail(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    order_id = int(callback.data.rsplit(":",1)[1])
    async with SessionLocal() as session:
        row = (await session.execute(
            select(Order, Service, User)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(Order.id == order_id)
        )).one_or_none()
        if not row:
            await callback.answer("درخواست پیدا نشد.", show_alert=True)
            return
        order, service, user = row
        docs = (await session.execute(
            select(Document).where(Document.order_id == order.id).order_by(Document.id)
        )).scalars().all()
        payments = (await session.execute(
            select(Payment).where(Payment.order_id == order.id).order_by(Payment.id.desc())
        )).scalars().all()
        data = json.loads(order.data_json or "{}")
    summary = (
        f"{status_header(order,service)}\n\n"
        f"👤 {data.get('full_name') or ((user.first_name or '')+' '+(user.last_name or '')).strip()}\n"
        f"📱 {data.get('mobile','')}\n"
        f"🆔 شناسه کاربری: {user.telegram_id}\n"
        f"💰 قیمت ثبت‌شده: {(order.price_snapshot_toman or service.price_toman):,} تومان\n"
        f"📎 مدارک: {len(docs)}\n"
        f"💳 پرداخت‌ها: {len(payments)}"
    )
    await callback.message.edit_text(summary, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 ارسال مدارک به من", callback_data=f"adm:docs:{order.id}")],
        [InlineKeyboardButton(text="💳 رسیدها", callback_data=f"adm:payments:{order.id}")],
        [InlineKeyboardButton(text="💬 پیام به مشترک", callback_data=f"adm:msg:{order.id}")],
        [InlineKeyboardButton(text="🟡 در حال انجام", callback_data=f"adm:status:{order.id}:in_progress")],
        [InlineKeyboardButton(text="⏳ منتظر مشترک", callback_data=f"adm:status:{order.id}:waiting_user")],
        [InlineKeyboardButton(text="✅ تکمیل درخواست", callback_data=f"adm:status:{order.id}:completed")],
        [InlineKeyboardButton(text="🔴 رد درخواست", callback_data=f"adm:status:{order.id}:rejected")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:orders")],
    ]))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:docs:"))
async def admin_order_docs(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    order_id = int(callback.data.rsplit(":",1)[1])
    async with SessionLocal() as session:
        docs = (await session.execute(
            select(Document).where(Document.order_id == order_id).order_by(Document.id)
        )).scalars().all()
    if not docs:
        await callback.answer("مدرکی ثبت نشده است.", show_alert=True)
        return
    for doc in docs:
        await callback.message.answer_photo(doc.telegram_file_id, caption=f"📎 {doc.document_type}")
    await callback.answer("مدارک ارسال شد.")


@router.callback_query(F.data.startswith("adm:payments:"))
async def admin_order_payments(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    order_id = int(callback.data.rsplit(":",1)[1])
    async with SessionLocal() as session:
        payments = (await session.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        )).scalars().all()
    if not payments:
        await callback.answer("رسیدی ثبت نشده است.", show_alert=True)
        return
    for payment in payments:
        if payment.receipt_file_id:
            await callback.message.answer_photo(
                payment.receipt_file_id,
                caption=f"💳 {payment.amount_toman:,} تومان | وضعیت: {PAYMENT_STATUS_TEXT.get(payment.status, 'نامشخص')}"
            )
    await callback.answer("رسیدها ارسال شد.")


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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{o.public_id} | {STATUS_TEXT.get(o.status,o.status)}", callback_data=f"adm:order:{o.id}")]
        for o,s,u in rows
    ] + [[InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:home")]])
    await callback.message.edit_text(text or "درخواستی ثبت نشده است.", reply_markup=keyboard)
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

    recipients = set(settings.admin_id_set)
    async with SessionLocal() as session:
        operators = (await session.execute(
            select(Operator).where(Operator.active.is_(True))
        )).scalars().all()
    for op in operators:
        if can_operator(op, "view_orders"):
            recipients.add(op.telegram_id)
    for recipient_id in recipients:
        op = None
        if recipient_id not in settings.admin_id_set:
            op = next((x for x in operators if x.telegram_id == recipient_id), None)
        await bot.send_message(recipient_id, text, reply_markup=order_actions(order.id, operator=op))
        if payment and payment.receipt_file_id:
            await bot.send_photo(
                recipient_id, payment.receipt_file_id, caption=f"🧾 رسید پرداخت {order.public_id}"
            )
        for doc in docs:
            await bot.send_photo(
                recipient_id, doc.telegram_file_id, caption=f"📎 {doc.document_type} | {order.public_id}"
            )


@router.callback_query(F.data.startswith("adm:status:"))
async def change_status(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    is_main = callback.from_user.id in get_settings().admin_id_set
    if not is_main and (operator is None or not can_operator(operator, "set_status")):
        await callback.answer("دسترسی تغییر وضعیت ندارید.", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[3] not in {"in_progress", "waiting_user", "completed", "rejected"}:
        await callback.answer("وضعیت نامعتبر است.", show_alert=True)
        return
    try:
        order_id = int(parts[2])
    except ValueError:
        await callback.answer("شناسه درخواست نامعتبر است.", show_alert=True)
        return
    new_status = parts[3]
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await callback.answer("درخواست پیدا نشد.", show_alert=True)
            return
        old_status = order.status
        order.status = new_status
        await session.commit()
        service = await session.get(Service, order.service_id)
        user = await session.get(User, order.user_id)
    await audit(callback.from_user.id, "status_changed", order_id, {"from": old_status, "to": new_status})
    await callback.answer(f"وضعیت به «{STATUS_TEXT.get(new_status, new_status)}» تغییر کرد.")
    if user:
        try:
            await callback.message.bot.send_message(
                user.telegram_id,
                f"📌 وضعیت درخواست {order.public_id} تغییر کرد.\nوضعیت جدید: {STATUS_TEXT.get(new_status, new_status)}",
            )
        except Exception:
            pass
    if service:
        try:
            await callback.message.edit_text(
                status_header(order, service),
                reply_markup=order_actions(order.id, operator=None if is_main else operator),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("adm:approve:"))
async def approve(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    is_main = callback.from_user.id in get_settings().admin_id_set
    if not is_main and (operator is None or not can_operator(operator, "approve_payment")):
        await callback.answer("دسترسی تأیید پرداخت ندارید.", show_alert=True)
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
    await audit(callback.from_user.id, "payment_approved", order_id, {"payment_id": payment.id})
    await callback.message.bot.send_message(
        user.telegram_id,
        f"✅ پرداخت درخواست {order.public_id} تأیید شد.\nدرخواست شما وارد مرحله انجام شد.",
    )
    await send_case_to_operator(callback.bot, order_id)


@router.callback_query(F.data.startswith("adm:reject:"))
async def reject(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    is_main = callback.from_user.id in get_settings().admin_id_set
    if not is_main and (operator is None or not can_operator(operator, "reject_payment")):
        await callback.answer("دسترسی رد پرداخت ندارید.", show_alert=True)
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
    await audit(callback.from_user.id, "payment_rejected", order_id, {"payment_id": payment.id})
    await callback.message.bot.send_message(
        user.telegram_id,
        f"❌ رسید درخواست {order.public_id} تأیید نشد.\n"
        "می‌توانید رسید صحیح را همین حالا دوباره ارسال کنید.",
        reply_markup=retry_keyboard,
    )


@router.callback_query(F.data.startswith("adm:msg:"))
async def start_message(callback: CallbackQuery, state: FSMContext) -> None:
    operator = await get_operator(callback.from_user.id)
    if callback.from_user.id not in get_settings().admin_id_set and (operator is None or not can_operator(operator, "message_user")):
        await callback.answer("دسترسی پیام به مشترک ندارید.", show_alert=True)
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    await state.update_data(admin_order_id=order_id)
    await state.set_state(AdminForm.send_message)
    await callback.answer()
    await callback.message.answer("💬 پیام خود را ارسال کنید. متن، عکس، فایل، ویدیو یا صوت قابل ارسال است.")


@router.message(AdminForm.send_message)
async def send_message_to_user(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in get_settings().admin_id_set:
        operator = await get_operator(message.from_user.id)
        if operator is None or not can_operator(operator, "message_user"):
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



def _operator_permissions(operator: Operator) -> set[str]:
    try:
        data = json.loads(operator.permissions_json or "{}")
        return {k for k, v in data.items() if v}
    except (TypeError, json.JSONDecodeError):
        return set()


async def get_operator(telegram_id: int) -> Operator | None:
    async with SessionLocal() as session:
        return (
            await session.execute(
                select(Operator).where(Operator.telegram_id == telegram_id, Operator.active.is_(True))
            )
        ).scalar_one_or_none()


def can_operator(operator: Operator, permission: str) -> bool:
    return permission in _operator_permissions(operator)


@router.callback_query(F.data == "adm:operators")
async def operators_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    async with SessionLocal() as session:
        rows = (await session.execute(select(Operator).order_by(Operator.id))).scalars().all()
    text = "👨‍💼 مدیریت اپراتورها\n\n"
    if rows:
        for op in rows:
            permission_labels = {"view_orders": "مشاهده درخواست‌ها", "approve_payment": "تأیید پرداخت", "reject_payment": "رد پرداخت", "set_status": "تغییر وضعیت", "message_user": "پیام به مشترک"}
            flags = "، ".join(permission_labels.get(x, x) for x in sorted(_operator_permissions(op))) or "بدون دسترسی"
            text += f"• {op.display_name or 'بدون نام'} | {op.telegram_id} | {'🟢' if op.active else '🔴'}\n  دسترسی: {flags}\n"
    else:
        text += "هنوز اپراتوری ثبت نشده است.\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن اپراتور", callback_data="adm:operator:add")],
        [InlineKeyboardButton(text="🔐 تنظیم دسترسی اپراتور", callback_data="adm:operator:perm")],
        [InlineKeyboardButton(text="🚫 غیرفعال کردن اپراتور", callback_data="adm:operator:remove")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:home")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "adm:operator:add")
async def operator_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.operator_add)
    await callback.answer()
    await callback.message.answer("👨‍💼 شناسه عددی تلگرام اپراتور را ارسال کنید:")


@router.message(AdminForm.operator_add)
async def operator_add_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("❌ شناسه باید فقط عدد باشد.")
        return
    telegram_id = int(raw)
    async with SessionLocal() as session:
        op = (await session.execute(select(Operator).where(Operator.telegram_id == telegram_id))).scalar_one_or_none()
        if op is None:
            session.add(Operator(
                telegram_id=telegram_id,
                display_name=str(telegram_id),
                role="operator",
                permissions_json=json.dumps({"view_orders": True, "approve_payment": False, "reject_payment": False, "set_status": True, "message_user": True}, ensure_ascii=False),
                active=True,
            ))
            msg = "✅ اپراتور اضافه شد."
        else:
            op.active = True
            msg = "✅ اپراتور دوباره فعال شد."
        await session.commit()
    await state.clear()
    await message.answer(msg, reply_markup=admin_menu())


PERMISSION_LABELS = {
    "view_orders": "مشاهده درخواست‌ها",
    "approve_payment": "تأیید پرداخت",
    "reject_payment": "رد پرداخت",
    "set_status": "تغییر وضعیت درخواست",
    "message_user": "ارسال پیام به مشترک",
}

PERMISSION_ICONS = {
    "view_orders": "👁",
    "approve_payment": "💳",
    "reject_payment": "❌",
    "set_status": "🔄",
    "message_user": "💬",
}


def operator_permission_keyboard(telegram_id: int, permissions: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for key in ("view_orders", "approve_payment", "reject_payment", "set_status", "message_user"):
        mark = "✅" if key in permissions else "⬜"
        rows.append([InlineKeyboardButton(
            text=f"{mark} {PERMISSION_ICONS[key]} {PERMISSION_LABELS[key]}",
            callback_data=f"adm:operator:perm:toggle:{telegram_id}:{key}",
        )])
    rows.append([
        InlineKeyboardButton(text="💾 ذخیره دسترسی‌ها", callback_data=f"adm:operator:perm:save:{telegram_id}"),
        InlineKeyboardButton(text="❌ انصراف", callback_data="adm:operators"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "adm:operator:perm")
async def operator_perm_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.operator_permission)
    async with SessionLocal() as session:
        operators = (await session.execute(
            select(Operator).order_by(Operator.active.desc(), Operator.id)
        )).scalars().all()
    if not operators:
        await callback.answer("هنوز اپراتوری ثبت نشده است.", show_alert=True)
        await callback.message.edit_text("👨‍💼 مدیریت اپراتورها", reply_markup=admin_menu())
        return
    buttons = [
        [InlineKeyboardButton(
            text=f"{'🟢' if op.active else '🔴'} {op.display_name or 'بدون نام'} | {op.telegram_id}",
            callback_data=f"adm:operator:perm:select:{op.telegram_id}",
        )]
        for op in operators
    ]
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm:operators")])
    await callback.answer()
    await callback.message.edit_text(
        "🔐 تنظیم دسترسی همکار\n\nلطفاً همکار موردنظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("adm:operator:perm:select:"))
async def operator_perm_select(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    try:
        telegram_id = int(callback.data.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("شناسه همکار نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        op = (await session.execute(
            select(Operator).where(Operator.telegram_id == telegram_id)
        )).scalar_one_or_none()
    if op is None:
        await callback.answer("همکار پیدا نشد.", show_alert=True)
        return
    try:
        permissions_data = json.loads(op.permissions_json or "{}")
    except (TypeError, json.JSONDecodeError):
        permissions_data = {}
    permissions = {key for key in PERMISSION_LABELS if permissions_data.get(key)}
    await state.set_state(AdminForm.operator_permission)
    await state.update_data(operator_permission_id=telegram_id, operator_permissions=list(permissions))
    await callback.answer()
    await callback.message.edit_text(
        f"🔐 تنظیم دسترسی همکار\n\n"
