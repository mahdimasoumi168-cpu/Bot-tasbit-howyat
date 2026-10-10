import json
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, or_, select, update

from app.bot.handlers import STATUS_TEXT, normalize_digits as normalize_digits_admin
from app.bot.states import AdminForm
from app.bot.keyboards import admin_cancel_menu
from app.core.config import get_settings
from app.db.models import AuditLog, Companion, Document, Order, Operator, Payment, Service, Setting, Ticket, TicketMessage, User, Wallet, WalletTransaction, WalletTopup, DiscountCode
from app.db.session import SessionLocal

router = Router()


def ui_button(text: str, **kwargs):
    """Create consistently styled Telegram inline buttons: blue by default, semantic red/green when appropriate."""
    if "style" not in kwargs:
        if any(token in text for token in ("❌", "رد", "حذف", "غیرفعال", "انصراف")):
            kwargs["style"] = "danger"
        elif any(token in text for token in ("✅", "تأیید", "ذخیره", "انجام", "فعال")):
            kwargs["style"] = "success"
        else:
            kwargs["style"] = "primary"
    return InlineKeyboardButton(text=text, **kwargs)


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
            [ui_button(text="🔵 رسیدهای در انتظار بررسی", callback_data="adm:pending")],
            [ui_button(text="📋 درخواست‌ها", callback_data="adm:orders")],
            [ui_button(text="🔎 پرونده با کد پیگیری", callback_data="adm:case")],
            [ui_button(text="📊 گزارش‌ها", callback_data="adm:stats")],
            [ui_button(text="👥 مشترکان", callback_data="adm:users")],
            [ui_button(text="👨‍💼 اپراتورها", callback_data="adm:operators")],
            [ui_button(text="🧩 خدمات", callback_data="adm:services")],
            [ui_button(text="💰 قیمت خدمات", callback_data="adm:prices")],
            [ui_button(text="💳 اطلاعات کارت", callback_data="adm:card")],
            [ui_button(text="💰 اعتبار مشترکان", callback_data="adm:wallets"), ui_button(text="➕ شارژهای در انتظار", callback_data="adm:topups")],
            [ui_button(text="🏷️ کدهای تخفیف", callback_data="adm:coupons")],
            [ui_button(text="⚙️ تنظیمات", callback_data="adm:settings")],
        ]
    )


def order_actions(
    order_id: int,
    operator: Operator | None = None,
    payment_review: bool = True,
    order_status: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    if payment_review and order_status == "waiting_receipt_review":
        if operator is None:
            rows.append([ui_button(text="✅ تأیید پرداخت", callback_data=f"adm:approve:{order_id}")])
            rows.append([ui_button(text="❌ رد پرداخت", callback_data=f"adm:reject:{order_id}")])
        else:
            if can_operator(operator, "approve_payment"):
                rows.append([ui_button(text="✅ تأیید پرداخت", callback_data=f"adm:approve:{order_id}")])
            if can_operator(operator, "reject_payment"):
                rows.append([ui_button(text="❌ رد پرداخت", callback_data=f"adm:reject:{order_id}")])
    if order_status in {"payment_approved", "in_progress", "waiting_user"}:
        if operator is None or can_operator(operator, "set_status"):
            rows.extend([
                [ui_button(text="🟡 در حال انجام", callback_data=f"adm:status:{order_id}:in_progress")],
                [ui_button(text="⏳ منتظر مشترک", callback_data=f"adm:status:{order_id}:waiting_user")],
                [ui_button(text="✅ تکمیل درخواست", callback_data=f"adm:status:{order_id}:completed")],
                [ui_button(text="🔴 رد درخواست", callback_data=f"adm:status:{order_id}:rejected")],
            ])
    if operator is None or can_operator(operator, "message_user"):
        rows.append([ui_button(text="💬 پیام به مشترک", callback_data=f"adm:msg:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def status_header(order: Order, service: Service) -> str:
    return f"{order.public_id} | {STATUS_TEXT.get(order.status, 'نامشخص')}\n🪪 خدمت: {service.name}"






async def ensure_wallet_admin(session, user_id: int) -> Wallet:
    wallet = (await session.execute(select(Wallet).where(Wallet.user_id == user_id))).scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance_toman=0)
        session.add(wallet)
        await session.flush()
    return wallet


@router.callback_query(F.data == "adm:wallets")
async def admin_wallets(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(User, Wallet).outerjoin(Wallet, Wallet.user_id == User.id)
            .order_by(User.id.desc()).limit(15)
        )).all()
    lines = ["💰 مدیریت اعتبار مشترکان", "", "برای ویرایش موجودی، مشترک را انتخاب کنید یا جست‌وجو را بزنید."]
    buttons = []
    for user, wallet in rows:
        balance = wallet.balance_toman if wallet else 0
        display_name = " ".join(x for x in (user.first_name, user.last_name) if x) or "بدون نام"
        lines.append(f"👤 {display_name} | 🆔 {user.telegram_id} | 💰 {balance:,} تومان")
        buttons.append([ui_button(
            text=f"✏️ {user.telegram_id} | {balance:,} تومان",
            callback_data=f"adm:wallet:edit:{user.telegram_id}",
        )])
    if not rows:
        lines.append("هنوز مشترکی ثبت نشده است.")
    buttons.extend([
        [ui_button(text="🔎 جست‌وجوی مشترک برای تغییر اعتبار", callback_data="adm:wallet:adjust")],
        [ui_button(text="➕ شارژهای در انتظار", callback_data="adm:topups")],
        [ui_button(text="🔙 بازگشت به مدیریت", callback_data="adm:home")],
    ])
    await callback.answer()
    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "adm:wallet:adjust")
async def admin_wallet_adjust_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.clear()
    await state.set_state(AdminForm.wallet_adjust_user)
    await callback.answer()
    await callback.message.answer(
        "🔎 مشترک موردنظر را پیدا کنید.\n\n"
        "شناسه عددی تلگرام، نام، نام کاربری یا شماره درخواست را وارد کنید.\n"
        "مثال: 8937359321 یا @username",
        reply_markup=admin_cancel_menu(),
    )


@router.callback_query(F.data.startswith("adm:wallet:edit:"))
async def admin_wallet_edit_user(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        telegram_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("شناسه مشترک نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if not user:
            await callback.answer("مشترک پیدا نشد.", show_alert=True)
            return
        wallet = await ensure_wallet_admin(session, user.id)
        balance = wallet.balance_toman
    await state.clear()
    await state.update_data(wallet_adjust_user_id=user.id, wallet_adjust_telegram_id=user.telegram_id)
    await state.set_state(AdminForm.wallet_adjust_amount)
    await callback.answer()
    await callback.message.answer(
        f"💰 تغییر اعتبار مشترک\n\n"
        f"👤 {user.first_name or ''} {user.last_name or ''}\n"
        f"🆔 {user.telegram_id}\n"
        f"موجودی فعلی: {balance:,} تومان\n\n"
        "مبلغ را با علامت وارد کنید:\n"
        "+50000 برای افزایش ۵۰٬۰۰۰ تومان\n"
        "-20000 برای کاهش ۲۰٬۰۰۰ تومان\n"
        "محدودیت: عدد صحیح، فقط تومان؛ موجودی منفی مجاز نیست.",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.wallet_adjust_user)
async def admin_wallet_adjust_find(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = normalize_digits_admin((message.text or "").strip())
    if not raw:
        await message.answer("عبارت جست‌وجو را وارد کنید.", reply_markup=admin_cancel_menu())
        return
    async with SessionLocal() as session:
        user = None
        if raw.isdigit():
            user = (await session.execute(
                select(User).where(User.telegram_id == int(raw))
            )).scalar_one_or_none()
        if user is None:
            pattern = f"%{raw.lstrip('@#')}%"
            user = (await session.execute(
                select(User).where(or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.username.ilike(pattern),
                )).order_by(User.id.desc()).limit(1)
            )).scalar_one_or_none()
        if user is None and raw.lstrip("#").isdigit():
            order = (await session.execute(
                select(Order).where(Order.public_id == f"#{raw.lstrip('#')}")
            )).scalar_one_or_none()
            if order:
                user = await session.get(User, order.user_id)
        if user is None:
            await message.answer("❌ مشترک پیدا نشد. شناسه عددی یا نام دیگری را امتحان کنید.", reply_markup=admin_cancel_menu())
            return
        wallet = await ensure_wallet_admin(session, user.id)
        balance = wallet.balance_toman
        user_id, telegram_id = user.id, user.telegram_id
        display_name = " ".join(x for x in (user.first_name, user.last_name) if x) or "بدون نام"
    await state.update_data(wallet_adjust_user_id=user_id, wallet_adjust_telegram_id=telegram_id)
    await state.set_state(AdminForm.wallet_adjust_amount)
    await message.answer(
        f"💰 تغییر اعتبار مشترک\n\n👤 {display_name}\n🆔 {telegram_id}\n"
        f"موجودی فعلی: {balance:,} تومان\n\n"
        "+50000 برای افزایش ۵۰٬۰۰۰ تومان\n"
        "-20000 برای کاهش ۲۰٬۰۰۰ تومان\n"
        "مبلغ را با + یا - و به تومان وارد کنید. موجودی منفی مجاز نیست.",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.wallet_adjust_amount)
async def admin_wallet_adjust_apply(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = normalize_digits_admin((message.text or "").replace(",", "").replace("٬", "").replace(" ", ""))
    if len(raw) < 2 or raw[0] not in "+-" or not raw[1:].isdigit() or int(raw[1:]) <= 0:
        await message.answer("❌ مبلغ معتبر نیست. نمونه: +50000 یا -20000", reply_markup=admin_cancel_menu())
        return
    delta = int(raw)
    data = await state.get_data()
    user_id = data.get("wallet_adjust_user_id")
    telegram_id = data.get("wallet_adjust_telegram_id")
    if not user_id or not telegram_id:
        await state.clear()
        await message.answer("❌ مشترک انتخاب نشده است؛ دوباره از مدیریت اعتبار شروع کنید.", reply_markup=admin_menu())
        return
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if not user or user.telegram_id != telegram_id:
            await state.clear()
            await message.answer("❌ اطلاعات مشترک پیدا نشد؛ دوباره جست‌وجو کنید.", reply_markup=admin_menu())
            return
        wallet = await ensure_wallet_admin(session, user.id)
        if wallet.balance_toman + delta < 0:
            await message.answer(
                f"❌ موجودی کافی نیست.\nموجودی فعلی: {wallet.balance_toman:,} تومان\n"
                f"کاهش درخواستی: {abs(delta):,} تومان",
                reply_markup=admin_cancel_menu(),
            )
            return
        # تغییر موجودی به‌صورت اتمی؛ جلوگیری از تداخل هم‌زمان پرداخت/شارژ
        # با اصلاح دستی مدیریت و جلوگیری از منفی‌شدن اعتبار.
        changed = await session.execute(
            update(Wallet)
            .where(
                Wallet.user_id == user.id,
                Wallet.balance_toman + delta >= 0,
            )
            .values(balance_toman=Wallet.balance_toman + delta)
        )
        if changed.rowcount != 1:
            await session.rollback()
            await message.answer(
                "❌ موجودی در همین لحظه تغییر کرده یا برای این کاهش کافی نیست. "
                "موجودی را دوباره بررسی کنید و مجدداً تلاش کنید.",
                reply_markup=admin_menu(),
            )
            return
        await session.refresh(wallet)
        new_balance = wallet.balance_toman
        session.add(WalletTransaction(
            user_id=user.id,
            amount_toman=delta,
            balance_after_toman=new_balance,
            kind="admin_adjustment",
            description=f"اصلاح اعتبار توسط مدیریت (شناسه {message.from_user.id})",
        ))
        session.add(AuditLog(
            actor_telegram_id=message.from_user.id,
            action="wallet_admin_adjustment",
            details_json=json.dumps({
                "target_telegram_id": telegram_id,
                "delta_toman": delta,
                "balance_after_toman": new_balance,
            }, ensure_ascii=False),
        ))
        await session.commit()
    await state.clear()
    action = "افزایش" if delta > 0 else "کاهش"
    await message.answer(
        f"✅ اعتبار مشترک با موفقیت {action} یافت.\n"
        f"🆔 شناسه: {telegram_id}\n"
        f"تغییر: {delta:+,} تومان\n"
        f"موجودی جدید: {new_balance:,} تومان",
        reply_markup=admin_menu(),
    )
    try:
        await message.bot.send_message(
            telegram_id,
            f"🔔 تغییر اعتبار حساب شما\n{action}: {abs(delta):,} تومان\nموجودی فعلی: {new_balance:,} تومان",
        )
    except Exception:
        pass


@router.callback_query(F.data == "adm:topups")
async def admin_topups(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True); return
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(WalletTopup, User).join(User, WalletTopup.user_id == User.id)
            .where(WalletTopup.status == "waiting_receipt_review")
            .order_by(WalletTopup.created_at.asc()).limit(30)
        )).all()
    if not rows:
        await callback.answer("شارژ در انتظار بررسی وجود ندارد.", show_alert=True); return
    buttons = [[ui_button(text=f"#{t.id} | {t.amount_toman:,} تومان | {u.telegram_id}", callback_data=f"adm:topup:view:{t.id}")] for t,u in rows]
    buttons.append([ui_button(text="🔙 بازگشت", callback_data="menu:admin")])
    await callback.answer()
    await callback.message.edit_text("➕ شارژهای در انتظار بررسی:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("adm:topup:view:"))
async def admin_topup_view(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True); return
    topup_id = int(callback.data.rsplit(":", 1)[1])
    async with SessionLocal() as session:
        row = (await session.execute(
            select(WalletTopup, User).join(User, WalletTopup.user_id == User.id).where(WalletTopup.id == topup_id)
        )).one_or_none()
    if not row:
        await callback.answer("شارژ پیدا نشد.", show_alert=True); return
    topup, user = row
    await callback.answer()
    await callback.message.edit_text(
        f"➕ شارژ اعتبار #{topup.id}\n👤 {user.first_name or ''} {user.last_name or ''}\n🆔 {user.telegram_id}\n💰 {topup.amount_toman:,} تومان",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [ui_button(text="✅ تأیید و افزایش اعتبار", callback_data=f"adm:topup:approve:{topup.id}")],
            [ui_button(text="❌ رد شارژ", callback_data=f"adm:topup:reject:{topup.id}")],
            [ui_button(text="🔙 بازگشت", callback_data="adm:topups")],
        ])
    )
    if topup.receipt_file_id:
        if topup.receipt_type == "document":
            await callback.message.answer_document(topup.receipt_file_id, caption=f"🧾 رسید شارژ #{topup.id}")
        else:
            await callback.message.answer_photo(topup.receipt_file_id, caption=f"🧾 رسید شارژ #{topup.id}")





@router.callback_query(F.data == "adm:coupons")
async def admin_coupons(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True); return
    async with SessionLocal() as session:
        rows = (await session.execute(select(DiscountCode).order_by(DiscountCode.created_at.desc()).limit(30))).scalars().all()
    lines = ["🏷️ کدهای تخفیف", ""]
    lines += [f"{x.code} | {'درصدی' if x.kind == 'percent' else 'مبلغی'} {x.value}{'%' if x.kind == 'percent' else ' تومان'} | {'فعال' if x.active else 'غیرفعال'} | مصرف: {x.used_count}" for x in rows]
    if not rows: lines.append("هنوز کدی ثبت نشده است.")
    await callback.answer()
    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [ui_button(text="➕ ایجاد کد تخفیف", callback_data="adm:coupon:add")],
        [ui_button(text="🔙 بازگشت", callback_data="menu:admin")],
    ]))


@router.callback_query(F.data == "adm:coupon:add")
async def admin_coupon_add(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set: return
    await state.set_state(AdminForm.discount_code)
    await callback.answer()
    await callback.message.edit_text("🏷️ کد تخفیف را وارد کنید.\nمثال: RENA20", reply_markup=admin_cancel_menu())


@router.message(AdminForm.discount_code)
async def admin_coupon_code(message: Message, state: FSMContext) -> None:
    if not is_admin(message): return
    code = (message.text or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]{3,64}", code):
        await message.answer("❌ کد تخفیف معتبر نیست.", reply_markup=admin_cancel_menu()); return
    await state.update_data(discount_code=code)
    await state.set_state(AdminForm.discount_value)
    await message.answer("💰 مقدار تخفیف را وارد کنید.\nمثال: 20%\nیا: 50000 تومان", reply_markup=admin_cancel_menu())


@router.message(AdminForm.discount_value)
async def admin_coupon_value(message: Message, state: FSMContext) -> None:
    if not is_admin(message): return
    raw = normalize_digits_admin(message.text or "").replace(",", "").replace("٬", "").strip()
    kind = "percent" if raw.endswith("%") else "fixed"
    raw = raw.rstrip("%").strip()
    if not raw.isdigit() or int(raw) <= 0 or (kind == "percent" and int(raw) > 100):
        await message.answer("❌ مقدار تخفیف معتبر نیست.", reply_markup=admin_cancel_menu()); return
    data = await state.get_data()
    code, value = data.get("discount_code"), int(raw)
    async with SessionLocal() as session:
        exists = (await session.execute(select(DiscountCode).where(DiscountCode.code == code))).scalar_one_or_none()
        if exists:
            exists.kind, exists.value, exists.active = kind, value, True
        else:
            session.add(DiscountCode(code=code, kind=kind, value=value, active=True))
        await session.commit()
    await state.clear()
    await message.answer("✅ کد تخفیف ذخیره و فعال شد.", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        operator = await get_operator(callback.from_user.id)
        if operator is None:
            await callback.answer("دسترسی ندارید.", show_alert=True)
            return
    await state.clear()
    await callback.answer("عملیات لغو شد.")
    await callback.message.edit_text(
        "❌ عملیات جاری لغو شد.\n\nبه پنل مدیریت برگشتید.",
        reply_markup=admin_menu(),
    )


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
        [ui_button(text="📋 درخواست‌های قابل رسیدگی", callback_data="op:orders")],
        [ui_button(text="🔎 جست‌وجوی پرونده با کد پیگیری", callback_data="op:case")],
        [ui_button(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
        [ui_button(text="🔙 بازگشت", callback_data="op:back")],
    ])
    await message.answer("👨‍💼 پنل اپراتور\n\nدسترسی‌های شما بر اساس تنظیمات مدیریت نمایش داده می‌شود.", reply_markup=keyboard)


@router.callback_query(F.data == "op:back")
async def operator_back(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None:
        return
    await callback.message.edit_text("👨‍💼 پنل اپراتور", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [ui_button(text="📋 درخواست‌های قابل رسیدگی", callback_data="op:orders")],
        [ui_button(text="🔎 جست‌وجوی پرونده با کد پیگیری", callback_data="op:case")],
        [ui_button(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
    ]))
    await callback.answer()


async def _show_operator_orders(callback: CallbackQuery, status_filter: str = "active") -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی مشاهده درخواست‌ها را ندارید.", show_alert=True)
        return
    filters = {
        "active": (["payment_approved", "in_progress", "waiting_user"], "📋 درخواست‌های فعال"),
        "completed": (["completed"], "✅ درخواست‌های تکمیل‌شده"),
        "rejected": (["rejected"], "❌ درخواست‌های ردشده"),
    }
    statuses, heading = filters.get(status_filter, filters["active"])
    await callback.answer()
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(Order, Service, User)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(Order.status.in_(statuses))
            .order_by(Order.updated_at.desc())
            .limit(30)
        )).all()
    text = heading + "\n\n"
    if rows:
        text += "\n".join(
            f"{o.public_id} | {STATUS_TEXT.get(o.status, 'نامشخص')} | {s.name}"
            for o, s, _u in rows
        )
    else:
        text += "پرونده‌ای در این بخش وجود ندارد."
    buttons = [
        [ui_button(text=f"{o.public_id} | {STATUS_TEXT.get(o.status, 'نامشخص')}", callback_data=f"op:order:{o.id}")]
        for o, _s, _u in rows
    ]
    buttons.extend([
        [ui_button(text="🟡 درخواست‌های فعال", callback_data="op:orders:active"),
         ui_button(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
        [ui_button(text="✅ تکمیل‌شده‌ها", callback_data="op:orders:completed"),
         ui_button(text="❌ ردشده‌ها", callback_data="op:orders:rejected")],
        [ui_button(text="🔙 بازگشت به پنل", callback_data="op:back")],
    ])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "op:orders")
async def operator_orders(callback: CallbackQuery) -> None:
    await _show_operator_orders(callback, "active")


@router.callback_query(F.data.startswith("op:orders:"))
async def operator_orders_filter(callback: CallbackQuery) -> None:
    status_filter = callback.data.rsplit(":", 1)[1]
    if status_filter not in {"active", "completed", "rejected"}:
        await callback.answer("فیلتر درخواست نامعتبر است.", show_alert=True)
        return
    await _show_operator_orders(callback, status_filter)


@router.callback_query(F.data.startswith("op:order:"))
async def operator_order_detail(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer("شماره پرونده نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        row = (await session.execute(
            select(Order, Service, User)
            .join(Service, Service.id == Order.service_id)
            .join(User, User.id == Order.user_id)
            .where(Order.id == order_id)
        )).one_or_none()
        if not row:
            await callback.answer("درخواست پیدا نشد.", show_alert=True)
            return
        order, service, user = row
        data = json.loads(order.data_json or "{}")
        docs = (await session.execute(
            select(Document).where(Document.order_id == order.id).order_by(Document.id)
        )).scalars().all()
        companions = (await session.execute(
            select(Companion).where(Companion.order_id == order.id).order_by(Companion.id)
        )).scalars().all()
        payment = (await session.execute(
            select(Payment).where(Payment.order_id == order.id).order_by(Payment.id.desc())
        )).scalars().first()
    summary = build_case_text(order, service, user, data, companions, docs, [payment] if payment else [])
    summary += (
        f"\n🆔 شناسه عددی تلگرام: {user.telegram_id}"
        f"\n🔗 نام کاربری: @{user.username if user.username else 'ندارد'}"
        f"\n💳 وضعیت پرداخت: {PAYMENT_STATUS_TEXT.get(payment.status, payment.status) if payment else 'ثبت نشده'}"
        f"\n🟡 مدارک در انتظار بررسی: {sum(1 for d in docs if getattr(d, 'review_status', 'pending') == 'pending')}"
        f"\n✅ مدارک تأییدشده: {sum(1 for d in docs if getattr(d, 'review_status', 'pending') == 'approved')}"
        f"\n❌ مدارک ردشده: {sum(1 for d in docs if getattr(d, 'review_status', 'pending') == 'rejected')}"
    )
    buttons = [[ui_button(text="📎 مشاهده مدارک پرونده", callback_data=f"op:docs:{order.id}")]]
    if payment and payment.receipt_file_id:
        buttons.append([ui_button(text="🧾 مشاهده رسید پرداخت", callback_data=f"op:receipt:{order.id}")])
    if can_operator(operator, "set_status") and order.status in {"payment_approved", "in_progress", "waiting_user"}:
        buttons.extend([
            [ui_button(text="🟡 در حال انجام", callback_data=f"adm:status:{order.id}:in_progress")],
            [ui_button(text="⏳ منتظر مشترک", callback_data=f"adm:status:{order.id}:waiting_user")],
            [ui_button(text="✅ تکمیل درخواست", callback_data=f"adm:status:{order.id}:completed")],
        ])
    if can_operator(operator, "message_user"):
        buttons.append([ui_button(text="💬 پیام به مشترک", callback_data=f"adm:msg:{order.id}")])
    buttons.append([ui_button(text="🔙 بازگشت", callback_data="op:orders")])
    await callback.message.edit_text(summary, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("op:docs:"))
async def operator_order_docs(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی مشاهده مدارک را ندارید.", show_alert=True)
        return
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer("شماره پرونده نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        docs = (await session.execute(
            select(Document).where(Document.order_id == order_id).order_by(Document.id)
        )).scalars().all()
    if not order or order.status not in {"payment_approved", "in_progress", "waiting_user", "completed", "rejected"}:
        await callback.answer("پرونده پرداخت‌شده‌ای برای مشاهده مدارک پیدا نشد.", show_alert=True)
        return
    if not docs:
        await callback.answer("برای این پرونده مدرکی ثبت نشده است.", show_alert=True)
        return
    await callback.answer("مدارک ارسال می‌شوند.")
    for doc in docs:
        try:
            await callback.message.answer_photo(
                doc.telegram_file_id,
                caption=f"📎 {doc.document_type} | {order.public_id}\nوضعیت مدرک: {DOCUMENT_STATUS_TEXT.get(getattr(doc, 'review_status', 'pending'), 'نامشخص')}",
                reply_markup=document_review_keyboard(doc, operator=operator),
            )
        except Exception:
            await callback.message.answer(f"⚠️ مدرک «{doc.document_type}» قابل نمایش نیست.")


@router.callback_query(F.data.startswith("op:receipt:"))
async def operator_order_receipt(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    if operator is None or not can_operator(operator, "view_orders"):
        await callback.answer("دسترسی مشاهده رسید را ندارید.", show_alert=True)
        return
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer("شماره پرونده نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        payment = (await session.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        )).scalars().first()
        order = await session.get(Order, order_id)
    if not order or not payment or not payment.receipt_file_id:
        await callback.answer("رسید پرداخت پیدا نشد.", show_alert=True)
        return
    await send_payment_receipt(callback.bot, callback.from_user.id, payment, f"🧾 رسید پرداخت {order.public_id}")
    await callback.answer("رسید ارسال شد.")


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
            .where(Payment.status == "pending", Order.status == "waiting_receipt_review")
            .order_by(Payment.id.desc()).limit(20)
        )).all()
    if not rows:
        await callback.message.edit_text("🔵 رسید در انتظار بررسی وجود ندارد.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [ui_button(text="🔙 بازگشت",callback_data="op:back")]
        ]))
        await callback.answer()
        return
    await callback.message.edit_text("🔵 رسیدهای در انتظار بررسی:")
    for payment, order, service, user in rows:
        await callback.message.answer(
            f"{status_header(order, service)}\n"
            f"👤 {user.first_name or ''} {user.last_name or ''}\n"
            f"💰 {payment.amount_toman:,} تومان",
            reply_markup=order_actions(order.id, operator=operator, order_status=order.status),
        )
        if payment.receipt_file_id:
            await send_payment_receipt(callback.bot, callback.from_user.id, payment, f"🧾 رسید {order.public_id}")
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
        [ui_button(text="📋 درخواست‌های قابل رسیدگی", callback_data="op:orders")],
        [ui_button(text="🔎 جست‌وجوی پرونده با کد پیگیری", callback_data="op:case")],
        [ui_button(text="🔵 رسیدهای در انتظار بررسی", callback_data="op:pending")],
        [ui_button(text="🔙 بازگشت به منوی اصلی", callback_data="op:back")],
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
        "💳 مرحله ۱ از ۲\nشماره کارت ۱۶ رقمی را فقط به صورت عددی ارسال کنید.\nمثال: 6037991234567890\nمحدودیت: دقیقاً ۱۶ رقم.",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.set_card_number)
async def set_card_number_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    value = (message.text or "").replace(" ", "").replace("-", "").strip()
    if not value.isdigit() or len(value) != 16:
        await message.answer("❌ شماره کارت باید دقیقاً ۱۶ رقم باشد. دوباره وارد کنید:", reply_markup=admin_cancel_menu())
        return
    await state.update_data(card_number=value)
    await state.set_state(AdminForm.set_card_holder)
    await message.answer("💳 مرحله ۲ از ۲\nنام صاحب کارت را وارد کنید.\nمثال: علی احمدی\nمحدودیت: ۳ تا ۸۰ نویسه.", reply_markup=admin_cancel_menu())


@router.message(AdminForm.set_card_holder)
async def set_card_holder_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    holder = (message.text or "").strip()
    if len(holder) < 2:
        await message.answer("❌ نام صاحب کارت معتبر نیست. دوباره وارد کنید:", reply_markup=admin_cancel_menu())
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
            [ui_button(text="✏️ ویرایش اطلاعات کارت", callback_data="adm:setcard")],
            [ui_button(text="🔙 بازگشت", callback_data="adm:home")],
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
            [ui_button(text="💳 اطلاعات کارت", callback_data="adm:card")],
            [ui_button(text="💰 قیمت خدمات", callback_data="adm:prices")],
            [ui_button(text="🧩 وضعیت خدمات", callback_data="adm:services")],
            [ui_button(text="🔙 بازگشت", callback_data="adm:home")],
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
        buttons.append([ui_button(
            text=f"{state_text} | {service.name}",
            callback_data=f"adm:toggle:{service.id}"
        )])
    buttons.append([ui_button(text="🔙 بازگشت", callback_data="adm:home")])
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
    await services_panel(callback)


@router.callback_query(F.data.in_({"adm:case", "op:case"}))
async def case_lookup_start(callback: CallbackQuery, state: FSMContext) -> None:
    is_main = callback.from_user.id in get_settings().admin_id_set
    operator = await get_operator(callback.from_user.id)
    if not is_main and (operator is None or not can_operator(operator, "view_orders")):
        await callback.answer("دسترسی مشاهده پرونده ندارید.", show_alert=True)
        return
    await state.clear()
    await state.set_state(AdminForm.case_lookup)
    await callback.answer()
    await callback.message.answer(
        "🔎 مشاهده پرونده کامل\n\n"
        "کد پیگیری را وارد کنید.\nمثال: #10001 یا 10001\nمحدودیت: فقط کد پیگیری عددی.",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.case_lookup)
async def case_lookup(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        operator = await get_operator(message.from_user.id)
        if operator is None or not can_operator(operator, "view_orders"):
            return
    raw = normalize_digits_admin((message.text or "").strip()).lstrip("#").strip()
    if not raw.isdigit():
        await message.answer("❌ کد پیگیری نامعتبر است. مثال: #10001", reply_markup=admin_cancel_menu())
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
            await message.answer("❌ پرونده‌ای با این کد پیگیری پیدا نشد. دوباره وارد کنید:", reply_markup=admin_cancel_menu())
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
        reply_markup=order_actions(order.id, order_status=order.status),
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


async def send_payment_receipt(bot, chat_id: int, payment: Payment, caption: str) -> None:
    if not payment.receipt_file_id:
        return
    if getattr(payment, "receipt_type", "photo") == "document":
        await bot.send_document(chat_id, payment.receipt_file_id, caption=caption)
    else:
        await bot.send_photo(chat_id, payment.receipt_file_id, caption=caption)


PAYMENT_STATUS_TEXT = {
    "pending": "در انتظار بررسی",
    "approved": "تأیید شده",
    "rejected": "رد شده",
    "superseded": "جایگزین شده",
}

DOCUMENT_STATUS_TEXT = {
    "pending": "در انتظار بررسی",
    "approved": "تأیید شده",
    "rejected": "رد شده",
}


def document_review_keyboard(document: Document, operator: Operator | None = None) -> InlineKeyboardMarkup | None:
    if getattr(document, "review_status", "pending") != "pending":
        return None
    if operator is not None and not can_operator(operator, "review_documents"):
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        ui_button(text="✅ تأیید مدرک", callback_data=f"adm:doc:approve:{document.id}"),
        ui_button(text="❌ رد مدرک", callback_data=f"adm:doc:reject:{document.id}"),
    ]])


def build_case_text(order: Order, service: Service, user: User, data: dict, companions, documents, payments) -> str:
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
            lines.append(f"• {p.status} — {p.amount_toman:,} تومان — {p.created_at.strftime('%Y/%m/%d %H:%M') if p.created_at else '—'}")
    else:
        lines.append("• پرداختی ثبت نشده است")
    lines.append("")
    lines.append("")
    lines.append("📎 وضعیت بررسی مدارک")
    if documents:
        lines.extend(
            f"• {d.document_type}: {DOCUMENT_STATUS_TEXT.get(getattr(d, 'review_status', 'pending'), 'نامشخص')}"
            for d in documents
        )
    else:
        lines.append("• مدرکی ثبت نشده است")
    return "\n".join(lines)


@router.callback_query(F.data == "adm:users")
async def users_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.user_search)
    await callback.answer()
    await callback.message.answer(
        "👥 جستجوی مشترک\n\nنام، نام کاربری، شناسه تلگرام یا شماره درخواست را وارد کنید.\nمثال: احمد محمدی، @username، 7165912028 یا #10001",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.user_search)
async def user_search(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = normalize_digits_admin((message.text or "").strip())
    if not raw:
        await message.answer("❌ عبارت جستجو را وارد کنید.", reply_markup=admin_cancel_menu())
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
            await message.answer("❌ مشترک پیدا نشد. نام، نام کاربری، شناسه تلگرام یا شماره درخواست را امتحان کنید:", reply_markup=admin_cancel_menu())
            return
        orders = (await session.execute(
            select(Order, Service).join(Service, Order.service_id == Service.id)
            .where(
                Order.user_id == user.id,
                Order.status.notin_(["draft", "waiting_payment"]),
            )
            .order_by(Order.id.desc()).limit(30)
        )).all()
    text = (
        "👤 اطلاعات مشترک\n\n"
        f"شناسه تلگرام: {user.telegram_id}\n"
        f"نام: {(user.first_name or '')} {(user.last_name or '')}".strip() +
        f"\nنام کاربری: @{user.username if user.username else 'ندارد'}\n\n"
        "📋 آخرین درخواست‌ها:\n"
    )
    text += "\n".join(
        f"{o.public_id} | {STATUS_TEXT.get(o.status, "نامشخص")} | {s.name}" for o, s in orders
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
            [ui_button(text="🪪 تغییر قیمت تثبیت هویت", callback_data="adm:setprice:identity")],
            [ui_button(text="📝 تغییر قیمت کد رهگیری خودنویس", callback_data="adm:setprice:khodnevis")],
            [ui_button(text="🔙 بازگشت به پنل", callback_data="adm:home")],
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
        "💰 مبلغ جدید را فقط به تومان و به صورت عددی ارسال کنید.\nمثال: 280000\nمحدودیت: عدد صحیح بزرگ‌تر از صفر.",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.set_price)
async def set_price_from_panel(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = normalize_digits_admin((message.text or "").replace(",", "").replace("٬", "").strip())
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("❌ مبلغ نامعتبر است. فقط عدد مثبت را ارسال کنید.", reply_markup=admin_cancel_menu())
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
    parts = normalize_digits_admin(message.text or "").split()
    if len(parts) != 3 or parts[1] not in {"identity", "khodnevis"} or not parts[2].isdigit():
        await message.answer("برای تغییر قیمت، از بخش «💰 قیمت خدمات» در پنل مدیریت استفاده کنید.")
        return
    price = int(parts[2])
    if price <= 0:
        await message.answer("❌ مبلغ باید بیشتر از صفر باشد.", reply_markup=admin_cancel_menu())
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
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    # پاسخ سریع به کلیک و استفاده از تجمیع SQL به‌جای بارگذاری تمام رکوردها؛
    # با بزرگ‌شدن پایگاه‌داده، گزارش مدیریت کند نمی‌شود.
    await callback.answer()
    async with SessionLocal() as session:
        status_rows = (await session.execute(
            select(Order.status, func.count(Order.id)).group_by(Order.status)
        )).all()
        counts = {status: int(count) for status, count in status_rows}
        orders_count = sum(counts.values())
        approved_count, revenue = (await session.execute(
            select(
                func.count(Payment.id),
                func.coalesce(func.sum(Payment.amount_toman), 0),
            ).where(Payment.status == "approved")
        )).one()
        users_count = int((await session.execute(
            select(func.count(User.id))
        )).scalar_one())
    lines = [
        "📊 گزارش کلی کمک‌یار مهاجر",
        "",
        f"👥 مشترکان: {users_count}",
        f"📋 کل درخواست‌ها: {orders_count}",
        f"🔵 پرداخت‌های تأییدشده: {int(approved_count)}",
        f"💰 مبلغ پرداخت‌های تأییدشده: {int(revenue):,} تومان",
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
            [ui_button(text="🔙 بازگشت", callback_data="adm:home")]
        ])
    )


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
        companions = (await session.execute(
            select(Companion).where(Companion.order_id == order.id).order_by(Companion.id)
        )).scalars().all()
    summary = build_case_text(order, service, user, data, companions, docs, payments)
    summary += (
        f"\n🆔 شناسه عددی تلگرام: {user.telegram_id}"
        f"\n🔗 نام کاربری: @{user.username if user.username else 'ندارد'}"
        f"\n📎 مدارک: {len(docs)} (در انتظار: {sum(1 for d in docs if getattr(d, 'review_status', 'pending') == 'pending')})"
    )
    order_buttons = [
        [ui_button(text="📎 ارسال مدارک به من", callback_data=f"adm:docs:{order.id}")],
        [ui_button(text="💳 رسیدها", callback_data=f"adm:payments:{order.id}")],
        [ui_button(text="💬 پیام به مشترک", callback_data=f"adm:msg:{order.id}")],
        [ui_button(text="🔙 بازگشت", callback_data="adm:orders")],
    ]
    if order.status in {"payment_approved", "in_progress", "waiting_user"}:
        order_buttons[3:3] = [
            [ui_button(text="🟡 در حال انجام", callback_data=f"adm:status:{order.id}:in_progress")],
            [ui_button(text="⏳ منتظر مشترک", callback_data=f"adm:status:{order.id}:waiting_user")],
            [ui_button(text="✅ تکمیل درخواست", callback_data=f"adm:status:{order.id}:completed")],
            [ui_button(text="🔴 رد درخواست", callback_data=f"adm:status:{order.id}:rejected")],
        ]
    await callback.message.edit_text(summary, reply_markup=InlineKeyboardMarkup(inline_keyboard=order_buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:docs:"))
async def admin_order_docs(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer("شماره پرونده نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        docs = (await session.execute(
            select(Document).where(Document.order_id == order_id).order_by(Document.id)
        )).scalars().all()
    if not docs:
        await callback.answer("مدرکی ثبت نشده است.", show_alert=True)
        return
    await callback.answer("مدارک ارسال می‌شوند.")
    for doc in docs:
        await callback.message.answer_photo(
            doc.telegram_file_id,
            caption=f"📎 {doc.document_type}\nوضعیت مدرک: {DOCUMENT_STATUS_TEXT.get(getattr(doc, 'review_status', 'pending'), 'نامشخص')}",
            reply_markup=document_review_keyboard(doc),
        )


@router.callback_query(F.data.startswith("adm:doc:"))
async def document_review_action(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[2] not in {"approve", "reject"}:
        await callback.answer("درخواست بررسی مدرک نامعتبر است.", show_alert=True)
        return
    is_main = callback.from_user.id in get_settings().admin_id_set
    operator = await get_operator(callback.from_user.id)
    if not is_main and (operator is None or not can_operator(operator, "review_documents")):
        await callback.answer("دسترسی بررسی مدارک ندارید.", show_alert=True)
        return
    try:
        document_id = int(parts[3])
    except ValueError:
        await callback.answer("شناسه مدرک نامعتبر است.", show_alert=True)
        return
    new_status = "approved" if parts[2] == "approve" else "rejected"
    async with SessionLocal() as session:
        document = await session.get(Document, document_id)
        if document is None:
            await callback.answer("مدرک پیدا نشد.", show_alert=True)
            return
        claim = await session.execute(
            update(Document)
            .where(Document.id == document_id, Document.review_status == "pending")
            .values(
                review_status=new_status,
                reviewed_by_telegram_id=callback.from_user.id,
                reviewed_at=__import__("datetime").datetime.now(),
            )
        )
        if claim.rowcount != 1:
            await session.rollback()
            await callback.answer("این مدرک قبلاً بررسی شده است.", show_alert=True)
            return
        order = await session.get(Order, document.order_id)
        user = await session.get(User, order.user_id) if order else None
        session.add(AuditLog(
            actor_telegram_id=callback.from_user.id,
            action=f"document_{new_status}",
            order_id=order.id if order else None,
            details_json=json.dumps({"document_id": document_id, "document_type": document.document_type}, ensure_ascii=False),
        ))
        await session.commit()
    await callback.answer("مدرک تأیید شد." if new_status == "approved" else "مدرک رد شد.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    if user and order:
        status_label = DOCUMENT_STATUS_TEXT[new_status]
        note = (
            f"📎 وضعیت مدرک «{document.document_type}» در پرونده {order.public_id}: {status_label}.\n"
            + ("نیازی به اقدام دیگری نیست." if new_status == "approved" else "لطفاً با پشتیبانی تماس بگیرید تا برای اصلاح مدرک راهنمایی شوید.")
        )
        try:
            await callback.bot.send_message(user.telegram_id, note)
        except Exception:
            pass


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
            await send_payment_receipt(callback.bot, callback.from_user.id, payment, f"💳 {payment.amount_toman:,} تومان | وضعیت: {PAYMENT_STATUS_TEXT.get(payment.status, 'نامشخص')}")
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
            .where(Payment.status == "pending", Order.status == "waiting_receipt_review")
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
            reply_markup=order_actions(order.id, order_status=order.status),
        )
        if payment.receipt_file_id:
            await send_payment_receipt(callback.bot, callback.from_user.id, payment, f"🧾 رسید {order.public_id}")
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
            .where(Order.status.notin_(["draft", "waiting_payment", "waiting_receipt_review"]))
            .order_by(Order.id.desc())
            .limit(20)
        )
        rows = result.all()
    text = "📋 آخرین درخواست‌های قابل رسیدگی:\n\n"
    text += "\n".join(
        f"{o.public_id} | {STATUS_TEXT.get(o.status, o.status)} | {s.name} | {u.telegram_id}"
        for o, s, u in rows
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [ui_button(text=f"{o.public_id} | {STATUS_TEXT.get(o.status,o.status)}", callback_data=f"adm:order:{o.id}")]
        for o,s,u in rows
    ] + [[ui_button(text="🔙 بازگشت", callback_data="adm:home")]])
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
        await bot.send_message(recipient_id, text, reply_markup=order_actions(order.id, operator=op, payment_review=bool(payment and payment.status == "pending"), order_status=order.status))
        if payment and payment.receipt_file_id:
            await send_payment_receipt(bot, recipient_id, payment, f"🧾 رسید پرداخت {order.public_id}")
        for doc in docs:
            await bot.send_photo(
                recipient_id,
                doc.telegram_file_id,
                caption=f"📎 {doc.document_type} | {order.public_id}\nوضعیت مدرک: {DOCUMENT_STATUS_TEXT.get(getattr(doc, 'review_status', 'pending'), 'نامشخص')}",
                reply_markup=document_review_keyboard(doc, operator=op),
            )


@router.callback_query(F.data.startswith("adm:approve:"))
async def approve(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    is_main = callback.from_user.id in get_settings().admin_id_set
    if not is_main and (operator is None or not can_operator(operator, "approve_payment")):
        await callback.answer("دسترسی تأیید پرداخت ندارید.", show_alert=True)
        return
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("شماره درخواست نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        payment = (await session.execute(
            select(Payment).where(Payment.order_id == order_id, Payment.status == "pending")
            .order_by(Payment.id.desc())
        )).scalars().first()
        if not order or not payment or order.status != "waiting_receipt_review":
            await callback.answer("این رسید دیگر در انتظار بررسی نیست.", show_alert=True)
            return
        # هر دو وضعیت را به‌صورت شرطی تغییر می‌دهیم تا دوبارکلیک/درخواست هم‌زمان
        # باعث تأیید تکراری یا ارسال زودهنگام پرونده نشود.
        order_claim = await session.execute(
            update(Order).where(Order.id == order_id, Order.status == "waiting_receipt_review")
            .values(status="payment_approved")
        )
        payment_claim = await session.execute(
            update(Payment).where(Payment.id == payment.id, Payment.status == "pending")
            .values(status="approved")
        )
        if order_claim.rowcount != 1 or payment_claim.rowcount != 1:
            await session.rollback()
            await callback.answer("این رسید هم‌زمان بررسی شده است؛ فهرست را تازه کنید.", show_alert=True)
            return
        payload = json.loads(order.data_json or "{}")
        code = payload.get("discount_code")
        if code:
            coupon = (await session.execute(select(DiscountCode).where(DiscountCode.code == code))).scalar_one_or_none()
            if coupon and coupon.active and (not coupon.expires_at or coupon.expires_at > __import__("datetime").datetime.now()) and (coupon.max_uses is None or coupon.used_count < coupon.max_uses):
                coupon.used_count += 1
        ticket = (await session.execute(select(Ticket).where(Ticket.order_id == order_id))).scalar_one_or_none()
        if ticket is None:
            session.add(Ticket(order_id=order_id, status="open"))
        await session.commit()
        user = await session.get(User, order.user_id)
    await callback.answer("پرداخت تأیید شد.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await audit(callback.from_user.id, "payment_approved", order_id, {"payment_id": payment.id})
    await callback.bot.send_message(
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
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("شماره درخواست نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        payment = (await session.execute(
            select(Payment).where(Payment.order_id == order_id, Payment.status == "pending")
            .order_by(Payment.id.desc())
        )).scalars().first()
        if not order or not payment or order.status != "waiting_receipt_review":
            await callback.answer("این رسید دیگر در انتظار بررسی نیست.", show_alert=True)
            return
        order_claim = await session.execute(
            update(Order).where(Order.id == order_id, Order.status == "waiting_receipt_review")
            .values(status="rejected")
        )
        payment_claim = await session.execute(
            update(Payment).where(Payment.id == payment.id, Payment.status == "pending")
            .values(status="rejected")
        )
        if order_claim.rowcount != 1 or payment_claim.rowcount != 1:
            await session.rollback()
            await callback.answer("این رسید هم‌زمان بررسی شده است؛ فهرست را تازه کنید.", show_alert=True)
            return
        user = await session.get(User, order.user_id)
        await session.commit()
    await callback.answer("رسید رد شد.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [ui_button(text="🧾 ارسال مجدد رسید", callback_data=f"retry_receipt:{order.id}")]
    ])
    await audit(callback.from_user.id, "payment_rejected", order_id, {"payment_id": payment.id})
    await callback.bot.send_message(
        user.telegram_id,
        f"❌ رسید درخواست {order.public_id} تأیید نشد.\n"
        "می‌توانید رسید صحیح را همین حالا دوباره ارسال کنید.",
        reply_markup=retry_keyboard,
    )





@router.callback_query(F.data.startswith("adm:topup:approve:"))
async def admin_topup_approve(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        topup_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("شناسه شارژ نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        topup = await session.get(WalletTopup, topup_id)
        if not topup:
            await callback.answer("شارژ پیدا نشد.", show_alert=True)
            return
        claim = await session.execute(
            update(WalletTopup)
            .where(
                WalletTopup.id == topup_id,
                WalletTopup.status == "waiting_receipt_review",
            )
            .values(status="approved", reviewed_at=__import__("datetime").datetime.now())
        )
        if claim.rowcount != 1:
            await session.rollback()
            await callback.answer("این شارژ قبلاً بررسی شده است؛ اعتبار دوباره افزایش نمی‌یابد.", show_alert=True)
            return
        wallet = await ensure_wallet_admin(session, topup.user_id)
        # افزایش موجودی به‌صورت اتمی تا تأیید هم‌زمان چند شارژ باعث
        # از دست رفتن یکی از افزایش‌ها نشود.
        await session.execute(
            update(Wallet)
            .where(Wallet.user_id == topup.user_id)
            .values(balance_toman=Wallet.balance_toman + topup.amount_toman)
        )
        await session.refresh(wallet)
        session.add(WalletTransaction(
            user_id=topup.user_id,
            amount_toman=topup.amount_toman,
            balance_after_toman=wallet.balance_toman,
            kind="topup",
            description=f"افزایش اعتبار #{topup.id}",
            topup_id=topup.id,
        ))
        user = await session.get(User, topup.user_id)
        new_balance = wallet.balance_toman
        amount = topup.amount_toman
        await session.commit()
    await audit(callback.from_user.id, "wallet_topup_approved", None, {"topup_id": topup_id, "amount_toman": amount})
    await callback.answer("اعتبار افزایش یافت.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.bot.send_message(
        user.telegram_id,
        f"✅ افزایش اعتبار تأیید شد.\n💰 مبلغ: {amount:,} تومان\n💳 موجودی جدید: {new_balance:,} تومان",
    )


@router.callback_query(F.data.startswith("adm:topup:reject:"))
async def admin_topup_reject(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        topup_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("شناسه شارژ نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        topup = await session.get(WalletTopup, topup_id)
        if not topup:
            await callback.answer("شارژ پیدا نشد.", show_alert=True)
            return
        claim = await session.execute(
            update(WalletTopup)
            .where(
                WalletTopup.id == topup_id,
                WalletTopup.status == "waiting_receipt_review",
            )
            .values(status="rejected", reviewed_at=__import__("datetime").datetime.now())
        )
        if claim.rowcount != 1:
            await session.rollback()
            await callback.answer("این شارژ قبلاً بررسی شده است؛ وضعیت تغییر نکرد.", show_alert=True)
            return
        user = await session.get(User, topup.user_id)
        amount = topup.amount_toman
        await session.commit()
    await audit(callback.from_user.id, "wallet_topup_rejected", None, {"topup_id": topup_id, "amount_toman": amount})
    await callback.answer("شارژ رد شد.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.bot.send_message(
        user.telegram_id,
        f"❌ رسید افزایش اعتبار #{topup_id} تأیید نشد.\n"
        "در صورت نیاز دوباره از بخش «اعتبار من» اقدام کنید.",
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
    await callback.message.answer("💬 پیام خود را ارسال کنید. متن، عکس، فایل، ویدیو یا صوت قابل ارسال است.", reply_markup=admin_cancel_menu())


@router.callback_query(F.data.startswith("adm:reply:"))
async def start_reply_to_user(callback: CallbackQuery, state: FSMContext) -> None:
    operator = await get_operator(callback.from_user.id)
    settings = get_settings()
    is_support = settings.support_telegram_id == callback.from_user.id
    if callback.from_user.id not in settings.admin_id_set and not is_support and (
        operator is None or not can_operator(operator, "message_user")
    ):
        await callback.answer("دسترسی پاسخ به مشترک ندارید.", show_alert=True)
        return
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("پرونده نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await callback.answer("پرونده پیدا نشد.", show_alert=True)
            return
    await state.clear()
    await state.update_data(admin_order_id=order_id)
    await state.set_state(AdminForm.send_message)
    await callback.answer()
    await callback.message.answer(
        f"↩️ پاسخ به مشترک | پرونده {order.public_id}\n"
        "پیام، عکس، فایل، ویدیو یا صوت خود را ارسال کنید.",
        reply_markup=admin_cancel_menu(),
    )


@router.message(AdminForm.send_message)
async def send_message_to_user(message: Message, state: FSMContext) -> None:
    settings = get_settings()
    if message.from_user.id not in settings.admin_id_set and message.from_user.id != settings.support_telegram_id:
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
        if not row:
            await state.clear()
            await message.answer("❌ درخواست پیدا نشد.")
            return
        order, service, user = row

        # پاسخ مدیریت نباید به وجود قبلیِ تیکت وابسته باشد.
        # اگر تیکت برای درخواست هنوز ساخته نشده یا قبلاً بسته شده، آن را
        # دوباره فعال می‌کنیم تا پیام مدیریت از بین نرود.
        if ticket is None:
            ticket = Ticket(order_id=order.id, status="open")
            session.add(ticket)
            await session.flush()
        elif ticket.status != "open":
            ticket.status = "open"
        file_id = None
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        elif message.video:
            file_id = message.video.file_id
        elif message.audio:
            file_id = message.audio.file_id
        elif message.voice:
            file_id = message.voice.file_id
        session.add(
            TicketMessage(
                ticket_id=ticket.id,
                sender_type="admin",
                sender_telegram_id=message.from_user.id,
                content_type=message.content_type,
                text=message.text or message.caption,
                file_id=file_id,
            )
        )
        await session.commit()
    # اعلان مستقل از خود محتوا: مشترک حتماً یک نوتیفیکیشن قابل مشاهده دریافت می‌کند.
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        ui_button(text="↩️ پاسخ به این پیام", callback_data=f"user:reply:{order.id}:{message.from_user.id}")
    ]])
    await message.bot.send_message(
        user.telegram_id,
        f"🔔 پیام جدید از پشتیبانی\n📋 درخواست: {order.public_id}\n\n"
        "برای پاسخ مستقیم به فرستنده، دکمه زیر را بزنید.",
        reply_markup=reply_keyboard,
    )
    await message.copy_to(user.telegram_id, reply_markup=reply_keyboard)
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
            permission_labels = {"view_orders": "مشاهده درخواست‌ها", "approve_payment": "تأیید پرداخت", "reject_payment": "رد پرداخت", "review_documents": "تأیید یا رد مدارک", "set_status": "تغییر وضعیت", "message_user": "پیام به مشترک"}
            flags = "، ".join(permission_labels.get(x, x) for x in sorted(_operator_permissions(op))) or "بدون دسترسی"
            text += f"• {op.display_name or 'بدون نام'} | {op.telegram_id} | {'🟢' if op.active else '🔴'}\n  دسترسی: {flags}\n"
    else:
        text += "هنوز اپراتوری ثبت نشده است.\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [ui_button(text="➕ افزودن اپراتور", callback_data="adm:operator:add")],
        [ui_button(text="🔐 تنظیم دسترسی اپراتور", callback_data="adm:operator:perm")],
        [ui_button(text="🚫 غیرفعال کردن اپراتور", callback_data="adm:operator:remove")],
        [ui_button(text="🔙 بازگشت", callback_data="adm:home")],
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
    await callback.message.answer("👨‍💼 شناسه عددی تلگرام اپراتور را ارسال کنید.\nمثال: 7165912028\nمحدودیت: فقط عدد.", reply_markup=admin_cancel_menu())


@router.message(AdminForm.operator_add)
async def operator_add_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = normalize_digits_admin((message.text or "").strip())
    if not raw.isdigit():
        await message.answer("❌ شناسه باید فقط عدد باشد.", reply_markup=admin_cancel_menu())
        return
    telegram_id = int(raw)
    async with SessionLocal() as session:
        op = (await session.execute(select(Operator).where(Operator.telegram_id == telegram_id))).scalar_one_or_none()
        if op is None:
            session.add(Operator(
                telegram_id=telegram_id,
                display_name=str(telegram_id),
                role="operator",
                permissions_json=json.dumps({"view_orders": True, "approve_payment": False, "reject_payment": False, "review_documents": True, "set_status": True, "message_user": True}, ensure_ascii=False),
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
    "review_documents": "تأیید یا رد مدارک",
    "set_status": "تغییر وضعیت درخواست",
    "message_user": "ارسال پیام به مشترک",
}

PERMISSION_ICONS = {
    "view_orders": "👁",
    "approve_payment": "💳",
    "reject_payment": "❌",
    "review_documents": "📎",
    "set_status": "🔄",
    "message_user": "💬",
}


def operator_permission_keyboard(telegram_id: int, permissions: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for key in ("view_orders", "approve_payment", "reject_payment", "review_documents", "set_status", "message_user"):
        mark = "✅" if key in permissions else "⬜"
        rows.append([ui_button(
            text=f"{mark} {PERMISSION_ICONS[key]} {PERMISSION_LABELS[key]}",
            callback_data=f"adm:operator:perm:toggle:{telegram_id}:{key}",
        )])
    rows.append([
        ui_button(text="💾 ذخیره دسترسی‌ها", callback_data=f"adm:operator:perm:save:{telegram_id}"),
        ui_button(text="❌ انصراف", callback_data="adm:operators"),
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
        [ui_button(
            text=f"{'🟢' if op.active else '🔴'} {op.display_name or 'بدون نام'} | {op.telegram_id}",
            callback_data=f"adm:operator:perm:select:{op.telegram_id}",
        )]
        for op in operators
    ]
    buttons.append([ui_button(text="🔙 بازگشت", callback_data="adm:operators")])
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
        f"شناسه: {telegram_id}\n"
        "دسترسی‌های فعال را با دکمه‌های زیر انتخاب کنید:",
        reply_markup=operator_permission_keyboard(telegram_id, permissions),
    )


@router.callback_query(F.data.startswith("adm:operator:perm:toggle:"))
async def operator_perm_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    parts = callback.data.split(":")
    if len(parts) != 6:
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return
    try:
        telegram_id = int(parts[4])
    except ValueError:
        await callback.answer("شناسه همکار نامعتبر است.", show_alert=True)
        return
    key = parts[5]
    if key not in PERMISSION_LABELS:
        await callback.answer("دسترسی نامعتبر است.", show_alert=True)
        return
    data = await state.get_data()
    if data.get("operator_permission_id") != telegram_id:
        await callback.answer("این تنظیمات منقضی شده است. دوباره وارد شوید.", show_alert=True)
        return
    permissions = set(data.get("operator_permissions") or [])
    if key in permissions:
        permissions.remove(key)
    else:
        permissions.add(key)
    await state.update_data(operator_permissions=list(permissions))
    await callback.message.edit_reply_markup(
        reply_markup=operator_permission_keyboard(telegram_id, permissions)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:operator:perm:save:"))
async def operator_perm_save(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    try:
        telegram_id = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer("شناسه همکار نامعتبر است.", show_alert=True)
        return
    data = await state.get_data()
    if data.get("operator_permission_id") != telegram_id:
        await callback.answer("این تنظیمات منقضی شده است. دوباره وارد شوید.", show_alert=True)
        return
    permissions = set(data.get("operator_permissions") or [])
    async with SessionLocal() as session:
        op = (await session.execute(
            select(Operator).where(Operator.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if op is None:
            await state.clear()
            await callback.answer("همکار پیدا نشد.", show_alert=True)
            return
        op.permissions_json = json.dumps(
            {key: key in permissions for key in PERMISSION_LABELS},
            ensure_ascii=False,
        )
        await session.commit()
    await state.clear()
    await callback.answer("دسترسی‌ها ذخیره شد.")
    await callback.message.edit_text(
        "✅ دسترسی‌های همکار با موفقیت ذخیره شد.",
        reply_markup=admin_menu(),
    )


@router.callback_query(F.data == "adm:operator:remove")
async def operator_remove_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in get_settings().admin_id_set:
        return
    await state.clear()
    await state.set_state(AdminForm.operator_remove)
    await callback.answer()
    await callback.message.answer("🚫 شناسه عددی اپراتور را برای غیرفعال‌سازی ارسال کنید.\nمثال: 7165912028\nمحدودیت: فقط عدد.", reply_markup=admin_cancel_menu())


@router.message(AdminForm.operator_remove)
async def operator_remove_save(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    raw = normalize_digits_admin((message.text or "").strip())
    if not raw.isdigit():
        await message.answer("❌ شناسه نامعتبر است.", reply_markup=admin_cancel_menu())
        return
    async with SessionLocal() as session:
        result = await session.execute(
            select(Operator).where(Operator.telegram_id == int(raw))
        )
        op = result.scalar_one_or_none()
        if op is None:
            await state.clear()
            await message.answer("❌ اپراتور پیدا نشد.", reply_markup=admin_menu())
            return
        op.active = False
        await session.commit()
    await state.clear()
    await message.answer("✅ اپراتور غیرفعال شد.", reply_markup=admin_menu())


@router.callback_query(F.data.startswith("adm:status:"))
async def operator_status_change(callback: CallbackQuery) -> None:
    operator = await get_operator(callback.from_user.id)
    is_main = callback.from_user.id in get_settings().admin_id_set
    if not is_main and (operator is None or not can_operator(operator, "set_status")):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    _, _, order_id_raw, status = callback.data.split(":", 3)
    try:
        order_id = int(order_id_raw)
    except ValueError:
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return
    allowed_statuses = {"in_progress", "waiting_user", "completed", "rejected"}
    if status not in allowed_statuses:
        await callback.answer("وضعیت نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await callback.answer("درخواست پیدا نشد.", show_alert=True)
            return
        if order.status not in {"payment_approved", "in_progress", "waiting_user"}:
            await callback.answer("این درخواست هنوز پرداخت تأییدشده ندارد یا قبلاً بسته شده است.", show_alert=True)
            return
        order.status = status
        user = await session.get(User, order.user_id)
        await session.commit()
    await audit(callback.from_user.id, "status_changed", order_id, {"status": status})
    labels = {"in_progress":"🟡 در حال انجام","waiting_user":"⏳ منتظر مشترک","completed":"✅ تکمیل شده","rejected":"🔴 رد شده"}
    await callback.answer("وضعیت تغییر کرد.")
    refreshed_operator = None if is_main else operator
    try:
        await callback.message.edit_reply_markup(
            reply_markup=order_actions(
                order_id,
                operator=refreshed_operator,
                payment_review=False,
                order_status=status,
            )
        )
    except Exception:
        pass
    completion_note = (
        f"\n\n🔖 کد پیگیری نهایی شما: {order.public_id}\n"
        "این کد را برای پیگیری‌های بعدی نگه دارید."
        if status == "completed" else ""
    )
    await callback.bot.send_message(
        user.telegram_id,
        f"🔔 وضعیت درخواست {order.public_id} تغییر کرد.\n\n"
        f"وضعیت جدید: {labels[status]}{completion_note}",
    )
