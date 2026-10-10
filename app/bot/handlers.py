import json
import re

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import delete, select, update

from app.bot.keyboards import (
    consulate_menu,
    document_type_menu,
    identity_document_type_menu,
    main_menu,
    optional_document_menu,
    yes_no_menu,
    cancel_menu,
    confirm_menu,
    support_menu,
    payment_choice_menu, wallet_menu, payment_invoice_menu,
)
from app.bot.states import IdentityForm, KhodnevisForm, RetryReceiptForm, SupportForm, PaymentForm, WalletTopupForm
from app.core.config import get_settings
from app.db.models import Companion, Document, Operator, Order, Payment, Service, ServiceCode, Setting, Ticket, TicketMessage, User, Wallet, WalletTransaction, WalletTopup, DiscountCode, AuditLog
from app.db.session import SessionLocal
from app.utils.dates import gregorian_display, jalali_to_gregorian
from app.utils.ids import public_order_id

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



async def safe_step_message(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Show the next form question even if editing the previous Telegram message fails."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)

async def is_active_operator(telegram_id: int) -> bool:
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Operator).where(
                    Operator.telegram_id == telegram_id,
                    Operator.active.is_(True),
                )
            )
        ).scalar_one_or_none()
        return row is not None


async def user_main_menu(telegram_id: int):
    return main_menu(
        telegram_id in get_settings().admin_id_set,
        await is_active_operator(telegram_id),
    )





async def get_wallet_balance(telegram_id: int) -> int:
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        if not user:
            return 0
        wallet = (await session.execute(select(Wallet).where(Wallet.user_id == user.id))).scalar_one_or_none()
        return int(wallet.balance_toman) if wallet else 0


async def ensure_wallet(session, user_id: int) -> Wallet:
    wallet = (await session.execute(select(Wallet).where(Wallet.user_id == user_id))).scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance_toman=0)
        session.add(wallet)
        await session.flush()
    return wallet


def calculate_discount(base_amount: int, coupon: DiscountCode | None) -> int:
    if coupon is None:
        return 0
    if coupon.kind == "percent":
        return min(base_amount, (base_amount * coupon.value) // 100)
    return min(base_amount, max(0, coupon.value))


async def order_amount_and_coupon(order_id: int) -> tuple[int, int, str | None]:
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if not order:
            raise ValueError("درخواست پیدا نشد.")
        data = json.loads(order.data_json or "{}")
        base = int(order.price_snapshot_toman or 0)
        coupon_code = data.get("discount_code")
        discount = 0
        if coupon_code:
            coupon = (await session.execute(select(DiscountCode).where(DiscountCode.code == coupon_code))).scalar_one_or_none()
            if coupon and coupon.active and (not coupon.expires_at or coupon.expires_at > __import__("datetime").datetime.now()) and (coupon.max_uses is None or coupon.used_count < coupon.max_uses):
                discount = calculate_discount(base, coupon)
            else:
                coupon_code = None
        return max(0, base - discount), discount, coupon_code


async def show_payment_options(message: Message, state: FSMContext, order_id: int) -> None:
    amount, discount, _code = await order_amount_and_coupon(order_id)
    form_data = await state.get_data()
    # Callback-confirmation messages belong to the bot, so use the saved user's ID,
    # not message.from_user.id, to avoid showing a false zero wallet balance.
    telegram_id = int(form_data.get("telegram_id") or message.from_user.id)
    credit = await get_wallet_balance(telegram_id)
    extra = f"\n🏷️ تخفیف: {discount:,} تومان" if discount else ""
    await state.set_state(PaymentForm.choice)
    await message.answer(
        f"💳 روش پرداخت را انتخاب کنید.\n\nمبلغ نهایی: {amount:,} تومان{extra}\n"
        f"💰 موجودی اعتبار شما: {credit:,} تومان\n\n"
        "اگر اعتبار کافی داشته باشید، می‌توانید مبلغ را از اعتبار کم کنید؛ در غیر این صورت کارت به کارت را انتخاب کنید.",
        reply_markup=payment_choice_menu(credit),
    )


async def apply_wallet_payment(telegram_id: int, order_id: int) -> bool:
    """Charge a wallet and approve its order exactly once, in one database transaction."""
    async with SessionLocal() as session:
        row = (await session.execute(
            select(Order, Service, User)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(Order.id == order_id, User.telegram_id == telegram_id)
        )).one_or_none()
        if not row:
            raise ValueError("درخواست پیدا نشد.")
        order, service, user = row
        if order.status != "waiting_payment":
            if order.status == "payment_approved":
                raise ValueError("پرداخت این درخواست قبلاً انجام شده است.")
            raise ValueError("این درخواست در حال حاضر قابل پرداخت نیست.")

        amount, _discount, code = await order_amount_and_coupon(order_id)
        wallet = await ensure_wallet(session, user.id)
        if wallet.balance_toman < amount:
            return False

        # Conditional update prevents a double click/retry from charging the same order twice.
        claimed = await session.execute(
            update(Order)
            .where(Order.id == order.id, Order.status == "waiting_payment")
            .values(status="payment_approved")
        )
        if claimed.rowcount != 1:
            await session.rollback()
            raise ValueError("وضعیت درخواست تغییر کرده است؛ لطفاً درخواست را دوباره بررسی کنید.")

        wallet.balance_toman -= amount
        # ثبت پرداخت کیف پول در جدول پرداخت‌ها نیز لازم است تا وضعیت پرداخت
        # در پرونده و پنل اپراتور درست نمایش داده شود.
        session.add(Payment(
            order_id=order.id,
            amount_toman=amount,
            receipt_file_id=None,
            receipt_type="wallet",
            status="approved",
        ))
        session.add(WalletTransaction(
            user_id=user.id,
            amount_toman=-amount,
            balance_after_toman=wallet.balance_toman,
            kind="order_payment",
            description=f"پرداخت {service.name} | {order.public_id}",
            order_id=order.id,
        ))
        if code:
            coupon = (await session.execute(
                select(DiscountCode).where(DiscountCode.code == code)
            )).scalar_one_or_none()
            if coupon and coupon.active and (
                coupon.max_uses is None or coupon.used_count < coupon.max_uses
            ):
                coupon.used_count += 1
        await session.commit()
        await audit_payment_event(telegram_id, "wallet_payment", order.id, amount)
        return True

async def audit_payment_event(actor_id: int, action: str, order_id: int, amount: int) -> None:
    async with SessionLocal() as session:
        session.add(AuditLog(actor_telegram_id=actor_id, action=action, order_id=order_id,
                             details_json=json.dumps({"amount_toman": amount}, ensure_ascii=False)))
        await session.commit()


STATUS_TEXT = {
    "draft": "پیش‌نویس",
    "waiting_payment": "در انتظار پرداخت",
    "waiting_receipt_review": "در انتظار بررسی رسید",
    "payment_approved": "پرداخت تأیید شده",
    "in_progress": "در حال انجام",
    "waiting_user": "در انتظار مشترک",
    "completed": "تکمیل شده",
    "rejected": "رد شده",
}


def normalize_digits(value: str) -> str:
    return value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


def normalize_mobile(value: str) -> str:
    digits = re.sub(r"\D", "", normalize_digits(value.strip()))
    if digits.startswith("0098"):
        digits = "98" + digits[4:]
    if digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "0" + digits
    return digits


def valid_mobile(value: str) -> bool:
    return bool(re.fullmatch(r"09\d{9}", normalize_mobile(value)))


def valid_name(value: str) -> bool:
    value = " ".join(value.split())
    if not 3 <= len(value) <= 80:
        return False
    return bool(re.fullmatch(r"[A-Za-zآ-یءئ‌]+(?:[ \-][A-Za-zآ-یءئ‌]+)+", value))


async def get_or_create_user(message: Message, telegram_id: int | None = None) -> User:
    uid = telegram_id or message.from_user.id
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == uid))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=uid,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if telegram_id is None:
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                user.username = message.from_user.username
                await session.commit()
        return user


async def create_order(message: Message, service_code: ServiceCode, telegram_id: int | None = None) -> Order:
    uid = telegram_id or message.from_user.id
    await get_or_create_user(message, telegram_id=telegram_id)
    async with SessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == uid))
        ).scalar_one()
        service = (
            await session.execute(select(Service).where(Service.code == service_code.value))
        ).scalar_one()
        if not service.enabled:
            raise ValueError("این خدمت در حال حاضر فعال نیست.")
        order = Order(
            public_id="PENDING",
            user_id=user.id,
            service_id=service.id,
            price_snapshot_toman=service.price_toman,
            data_json="{}",
        )
        session.add(order)
        await session.flush()
        order.public_id = public_order_id(order.id)
        await session.commit()
        await session.refresh(order)
        return order


async def payment_instructions(order_id: int) -> str:
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            raise ValueError("درخواست پیدا نشد.")
        service = await session.get(Service, order.service_id)
        if service is None:
            raise ValueError("خدمت درخواست پیدا نشد.")
        number = (
            await session.execute(select(Setting).where(Setting.key == "card_number"))
        ).scalar_one_or_none()
        holder = (
            await session.execute(select(Setting).where(Setting.key == "card_holder"))
        ).scalar_one_or_none()
    card_number = number.value if number and number.value else "هنوز توسط مدیریت تنظیم نشده است"
    card_holder = holder.value if holder and holder.value else "هنوز توسط مدیریت تنظیم نشده است"
    amount_toman, discount, _ = await order_amount_and_coupon(order_id)
    amount_rial = amount_toman * 10
    return (
        "🧾 فاکتور پرداخت\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 خدمت: {service.name}\n"
        f"🔢 شماره درخواست: {order.public_id}\n\n"
        "💰 مبلغ قابل پرداخت\n"
        f"تومان: <code>{amount_toman:,}</code> تومان\n"
        + (f"🏷️ تخفیف: {discount:,} تومان\n" if discount else "")
        + f"ریال: <code>{amount_rial}</code>\n\n"
        "💳 اطلاعات کارت\n"
        f"شماره کارت: <code>{card_number}</code>\n"
        f"به نام: {card_holder}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، تصویر رسید را ارسال کنید."
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, telegram_id: int | None = None) -> None:
    uid = telegram_id or message.from_user.id
    await state.clear()
    await get_or_create_user(message, telegram_id=telegram_id)
    await message.answer(
        "سلام 🌷\nبه «کمک‌یار مهاجر» خوش آمدید.\n\nخدمت موردنظر را انتخاب کنید:",
        reply_markup=await user_main_menu(uid),
    )


@router.message(F.text == "🔄 شروع مجدد")
async def restart(message: Message, state: FSMContext, telegram_id: int | None = None) -> None:
    # «شروع مجدد» دقیقاً همان رفتار /start را اجرا می‌کند.
    await start(message, state, telegram_id=telegram_id)


@router.callback_query(F.data == "menu:restart")
async def inline_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await restart(callback.message, state, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "flow:cancel")
async def flow_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("عملیات لغو شد.")
    await callback.message.edit_text(
        "❌ عملیات جاری لغو شد.\n\nبه منوی اصلی برگشتید.",
        reply_markup=await user_main_menu(callback.from_user.id),
    )

@router.callback_query(F.data == "menu:identity")
async def inline_identity(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await identity_start(callback.message, state, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "menu:khodnevis")
async def inline_khodnevis(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await khodnevis_start(callback.message, state, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "menu:tracking")
async def inline_tracking(callback: CallbackQuery) -> None:
    await callback.answer()
    await track_orders(callback.message, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "menu:account")
async def inline_account(callback: CallbackQuery) -> None:
    await callback.answer()
    await account(callback.message, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "menu:support")
async def inline_support(callback: CallbackQuery) -> None:
    await callback.answer()
    await support(callback.message, telegram_id=callback.from_user.id, show_direct=True)


@router.callback_query(F.data == "menu:support_orders")
async def inline_support_orders(callback: CallbackQuery) -> None:
    await callback.answer()
    await support(callback.message, telegram_id=callback.from_user.id, show_direct=False)

@router.callback_query(F.data == "identity:doc:amayesh")
async def inline_identity_doc_amayesh(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.identity_document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer()
    await state.update_data(identity_document_type="کارت آمایش")
    await state.set_state(IdentityForm.identity_document)
    await safe_step_message(callback, "📸 عکس کارت آمایش را ارسال کنید.\nمثال: عکس واضح و کامل از کارت.", reply_markup=cancel_menu())


@router.callback_query(F.data == "identity:doc:passport")
async def inline_identity_doc_passport(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.identity_document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer()
    await state.update_data(identity_document_type="پاسپورت")
    await state.set_state(IdentityForm.identity_document)
    await safe_step_message(callback, "📸 عکس صفحه اول پاسپورت را ارسال کنید.\nمثال: عکس واضح و کامل از صفحه مشخصات.", reply_markup=cancel_menu())


@router.callback_query(F.data == "identity:doc:other")
async def inline_identity_doc_other(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.identity_document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer()
    await safe_step_message(callback, "✍️ نوع مدرک را وارد کنید.\nمثال: کارت اقامت", reply_markup=cancel_menu())


@router.callback_query(F.data == "identity:doc:none")
async def inline_identity_doc_none(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.identity_document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer()
    await state.update_data(identity_document_type="ندارد", identity_document=None)
    await state.set_state(IdentityForm.tazkira)
    await safe_step_message(callback, "۷/۸\n📸 لطفاً عکس واضحِ تذکره اصلی یکی از اقارب نزدیک را ارسال کنید.\nمثال: تصویر کامل و خوانای تذکره اصلی پدر، مادر، برادر یا خواهر.", reply_markup=cancel_menu())


@router.message(IdentityForm.identity_document_type)
async def identity_document_type_text(message: Message, state: FSMContext) -> None:
    value = " ".join((message.text or "").split())
    if not value or len(value) > 80:
        await message.answer("❌ نوع مدرک را وارد کنید.", reply_markup=cancel_menu())
        return
    await state.update_data(identity_document_type=value)
    await state.set_state(IdentityForm.identity_document)
    await message.answer("📸 عکس این مدرک را ارسال کنید.\nمثال: عکس واضح و کامل از مدرک.", reply_markup=cancel_menu())


@router.callback_query(F.data == "identity:consulate:z")
async def inline_consulate_z(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.consulate:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(consulate="🇦🇫 زاهدان"); await state.set_state(IdentityForm.identity_document_type)
    await safe_step_message(callback, "۶/۸\nمدرک شناسایی شما چیست؟", reply_markup=identity_document_type_menu())

@router.callback_query(F.data == "identity:consulate:m")
async def inline_consulate_m(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.consulate:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(consulate="🇦🇫 مشهد"); await state.set_state(IdentityForm.identity_document_type)
    await safe_step_message(callback, "۶/۸\nمدرک شناسایی شما چیست؟", reply_markup=identity_document_type_menu())

@router.callback_query(F.data == "identity:companion:y")
async def inline_companion_yes(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.companion_choice:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.set_state(IdentityForm.companion_name)
    await safe_step_message(callback, "✍️ نام و نام خانوادگی همراه را وارد کنید.", reply_markup=cancel_menu())

@router.callback_query(F.data == "identity:companion:n")
async def inline_companion_no(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.companion_choice:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await show_identity_summary(callback.message, state)

@router.callback_query(F.data == "khodnevis:doc:amayesh")
async def inline_doc_amayesh(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != KhodnevisForm.document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(document_type="کارت آمایش"); await state.set_state(KhodnevisForm.amayesh)
    await safe_step_message(callback, "۴/۷\n📸 عکس کارت آمایش را ارسال کنید.\nمثال: عکس واضح از تمام کارت.\nمحدودیت: فقط عکس، واضح و خوانا.", reply_markup=cancel_menu())

@router.callback_query(F.data == "khodnevis:doc:passport")
async def inline_doc_passport(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != KhodnevisForm.document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(document_type="پاسپورت"); await state.set_state(KhodnevisForm.passport_first)
    await safe_step_message(callback, "۴/۷\n📸 عکس صفحه اول پاسپورت را ارسال کنید.\nمثال: عکس واضح از صفحه مشخصات.\nمحدودیت: فقط عکس، واضح و خوانا؛ این صفحه الزامی است.", reply_markup=cancel_menu())

@router.callback_query(F.data.startswith("khodnevis:optional:"))
async def inline_optional_document(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state(); action = callback.data.rsplit(":", 1)[1]
    if current not in {KhodnevisForm.passport_renewal, KhodnevisForm.residence_renewal}:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer()
    if action == "send":
        target = "صفحه تمدید پاسپورت" if current == KhodnevisForm.passport_renewal else "صفحه تمدید اقامت/ویزا"
        await callback.message.edit_text(f"📸 تصویر {target} را ارسال کنید.", reply_markup=cancel_menu()); return
    if current == KhodnevisForm.passport_renewal:
        await state.update_data(passport_renewal=None); await state.set_state(KhodnevisForm.residence_renewal)
        await safe_step_message(callback, "صفحه تمدید اقامت/ویزا را دارید؟", reply_markup=optional_document_menu())
    else:
        await state.update_data(residence_renewal=None); await state.set_state(KhodnevisForm.own_mobile)
        await safe_step_message(callback, "📱 شماره موبایل به نام خود شخص را ارسال کنید.", reply_markup=cancel_menu())

@router.callback_query(F.data == "order:confirm")
async def inline_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current == IdentityForm.confirm:
        await callback.answer(); await identity_confirm(callback.message, state)
    elif current == KhodnevisForm.confirm:
        await callback.answer(); await khodnevis_confirm(callback.message, state)
    else:
        await callback.answer("این تأیید دیگر فعال نیست.", show_alert=True)


@router.message(F.text == "🪪 تثبیت هویت")
async def identity_start(message: Message, state: FSMContext, telegram_id: int | None = None) -> None:
    uid = telegram_id or message.from_user.id
    await state.clear()
    try:
        order = await create_order(message, ServiceCode.IDENTITY, telegram_id=telegram_id)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=await user_main_menu(uid))
        return
    await state.update_data(
        order_id=order.id, public_id=order.public_id, service_code=ServiceCode.IDENTITY.value,
        telegram_id=uid,
    )
    await state.set_state(IdentityForm.full_name)
    await message.answer("۱/۸\nنام و نام خانوادگی را وارد کنید.\nمثال: احمد محمدی\nمحدودیت: ۳ تا ۸۰ نویسه و حداقل دو بخش.", reply_markup=cancel_menu())


@router.message(IdentityForm.full_name)
async def identity_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_name(value):
        await message.answer("❌ نام و نام خانوادگی باید بین ۳ تا ۸۰ نویسه باشد و حداقل شامل دو بخش باشد. مثال: «احمد محمدی».", reply_markup=cancel_menu())
        return
    await state.update_data(full_name=" ".join(value.split()))
    await state.set_state(IdentityForm.mobile)
    await message.answer("۲/۸\nشماره موبایل در دسترس را وارد کنید.\nمثال: 09123456789\nمحدودیت: فقط شماره موبایل ایران ۱۱ رقمی.", reply_markup=cancel_menu())


@router.message(IdentityForm.mobile)
async def identity_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست. مثال: 09123456789", reply_markup=cancel_menu())
        return
    await state.update_data(mobile=normalize_mobile(value))
    await state.set_state(IdentityForm.birth_date)
    await message.answer("۳/۸\nتاریخ تولد را به شمسی وارد کنید.\nمثال: ۱۳۷۵/۰۵/۲۰", reply_markup=cancel_menu())


@router.message(IdentityForm.birth_date)
async def identity_birth(message: Message, state: FSMContext) -> None:
    try:
        raw = normalize_digits(message.text or "").strip()
        if not re.fullmatch(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}", raw):
            raise ValueError("فرمت تاریخ باید مانند ۱۴۰۵/۰۱/۱۵ باشد.")
        year = int(re.split(r"[/-]", raw)[0])
        if not 1300 <= year <= 1500:
            raise ValueError("سال تاریخ باید بین ۱۳۰۰ تا ۱۵۰۰ باشد.")
        value = jalali_to_gregorian(raw)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=cancel_menu())
        return
    await state.update_data(birth_date_gregorian=gregorian_display(value))
    await state.set_state(IdentityForm.return_date)
    await message.answer("۴/۸\nآخرین تاریخ بازگشت به افغانستان را به شمسی وارد کنید.\nمثال: ۱۴۰۵/۰۱/۱۵", reply_markup=cancel_menu())


@router.message(IdentityForm.return_date)
async def identity_return(message: Message, state: FSMContext) -> None:
    try:
        raw = normalize_digits(message.text or "").strip()
        if not re.fullmatch(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}", raw):
            raise ValueError("فرمت تاریخ باید مانند ۱۴۰۵/۰۱/۱۵ باشد.")
        year = int(re.split(r"[/-]", raw)[0])
        if not 1300 <= year <= 1500:
            raise ValueError("تاریخ واردشده معتبر نیست.")
        value = jalali_to_gregorian(raw)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=cancel_menu())
        return
    await state.update_data(return_date_gregorian=gregorian_display(value))
    await state.set_state(IdentityForm.consulate)
    await message.answer("۵/۸\nکنسولگری را انتخاب کنید:", reply_markup=consulate_menu())


@router.message(IdentityForm.consulate)
async def identity_consulate(message: Message, state: FSMContext) -> None:
    if message.text not in {"🇦🇫 زاهدان", "🇦🇫 مشهد"}:
        await message.answer("لطفاً یکی از دو گزینه را انتخاب کنید.", reply_markup=consulate_menu())
        return
    await state.update_data(consulate=message.text)
    await state.set_state(IdentityForm.identity_document_type)
    await message.answer("۶/۸\nمدرک شناسایی شما چیست؟", reply_markup=identity_document_type_menu())


@router.message(IdentityForm.identity_document, F.photo)
async def identity_document(message: Message, state: FSMContext) -> None:
    await state.update_data(identity_document=message.photo[-1].file_id)
    await state.set_state(IdentityForm.tazkira)
    await message.answer("۷/۸\n📸 لطفاً عکس واضحِ تذکره اصلی یکی از اقارب نزدیک را ارسال کنید.\nمثال: تصویر کامل و خوانای تذکره اصلی پدر، مادر، برادر یا خواهر.\nمحدودیت: فقط عکس واضح و خوانا.", reply_markup=cancel_menu())


@router.message(IdentityForm.tazkira, F.photo)
async def identity_tazkira(message: Message, state: FSMContext) -> None:
    await state.update_data(tazkira=message.photo[-1].file_id)
    await state.set_state(IdentityForm.companion_choice)
    await message.answer("۸/۸\nآیا همراه دیگری دارید؟", reply_markup=yes_no_menu())


@router.message(IdentityForm.companion_choice)
async def identity_companion_choice(message: Message, state: FSMContext) -> None:
    if message.text == "✅ بله":
        await state.set_state(IdentityForm.companion_name)
        await message.answer("نام و نام خانوادگی همراه را وارد کنید.\nمثال: محمد احمدی\nمحدودیت: ۳ تا ۸۰ نویسه و حداقل دو بخش.", reply_markup=cancel_menu())
    elif message.text == "❌ خیر":
        await show_identity_summary(message, state)
    else:
        await message.answer("لطفاً «بله» یا «خیر» را انتخاب کنید.", reply_markup=yes_no_menu())


@router.message(IdentityForm.companion_name)
async def identity_companion_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 3:
        await message.answer("❌ نام همراه معتبر نیست. مثال: «محمد احمدی». محدودیت: ۳ تا ۸۰ نویسه و حداقل دو بخش.", reply_markup=cancel_menu())
        return
    await state.update_data(pending_companion_name=value)
    await state.set_state(IdentityForm.companion_mobile)
    await message.answer("شماره موبایل همراه را وارد کنید.\nمثال: 09123456789\nمحدودیت: فقط شماره موبایل ایران ۱۱ رقمی.", reply_markup=cancel_menu())


@router.message(IdentityForm.companion_mobile)
async def identity_companion_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست.", reply_markup=cancel_menu())
        return
    data = await state.get_data()
    companions = data.get("companions", [])
    companions.append({"full_name": data["pending_companion_name"], "mobile": normalize_mobile(value)})
    await state.update_data(companions=companions, pending_companion_name=None)
    await state.set_state(IdentityForm.companion_choice)
    await message.answer("آیا همراه دیگری دارید؟", reply_markup=yes_no_menu())


async def show_identity_summary(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    companions = data.get("companions", [])
    companion_text = "ندارد" if not companions else "\n".join(
        f"• {item['full_name']} — {item['mobile']}" for item in companions
    )
    await state.set_state(IdentityForm.confirm)
    await message.answer(
        "📋 خلاصه درخواست\n\n"
        f"نام: {data.get('full_name')}\n"
        f"موبایل: {data.get('mobile')}\n"
        f"تاریخ تولد: {data.get('birth_date_gregorian')}\n"
        f"آخرین بازگشت: {data.get('return_date_gregorian')}\n"
        f"کنسولگری: {data.get('consulate')}\n"
        f"همراهان:\n{companion_text}\n\n"
        "اگر اطلاعات درست است «تأیید و ادامه» را بزنید.",
        reply_markup=confirm_menu(),
    )


@router.message(IdentityForm.confirm, F.text == "✅ تأیید و ادامه")
async def identity_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await save_order_data(data)
    await show_payment_options(message, state, data["order_id"])


@router.message(IdentityForm.receipt, F.photo)
@router.message(IdentityForm.receipt, F.document)
async def identity_receipt(message: Message, state: FSMContext) -> None:
    try:
        await save_receipt(message, state)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=cancel_menu())
        return
    await state.clear()
    await message.answer("✅ رسید شما ثبت شد و برای بررسی ارسال گردید.", reply_markup=await user_main_menu(message.from_user.id))


@router.message(F.text == "📝 کد رهگیری خودنویس")
async def khodnevis_start(message: Message, state: FSMContext, telegram_id: int | None = None) -> None:
    uid = telegram_id or message.from_user.id
    await state.clear()
    try:
        order = await create_order(message, ServiceCode.KHODNEVIS, telegram_id=telegram_id)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=await user_main_menu(uid))
        return
    await state.update_data(
        order_id=order.id, public_id=order.public_id, service_code=ServiceCode.KHODNEVIS.value,
        telegram_id=uid,
    )
    await state.set_state(KhodnevisForm.full_name)
    await message.answer("۱/۷\nنام و نام خانوادگی را وارد کنید.\nمثال: احمد محمدی\nمحدودیت: ۳ تا ۸۰ نویسه و حداقل دو بخش.", reply_markup=cancel_menu())


@router.message(KhodnevisForm.full_name)
async def khodnevis_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 3:
        await message.answer("❌ نام و نام خانوادگی معتبر نیست. مثال: «احمد محمدی». محدودیت: ۳ تا ۸۰ نویسه و حداقل دو بخش.", reply_markup=cancel_menu())
        return
    await state.update_data(full_name=value)
    await state.set_state(KhodnevisForm.mobile)
    await message.answer("۲/۷\nشماره موبایل در دسترس را وارد کنید.\nمثال: 09123456789\nمحدودیت: فقط شماره موبایل ایران ۱۱ رقمی.", reply_markup=cancel_menu())


@router.message(KhodnevisForm.mobile)
async def khodnevis_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست. مثال: 09123456789", reply_markup=cancel_menu())
        return
    await state.update_data(mobile=normalize_mobile(value))
    await state.set_state(KhodnevisForm.document_type)
    await message.answer("۳/۷\nمدرک را انتخاب کنید:", reply_markup=document_type_menu())


@router.message(KhodnevisForm.document_type)
async def khodnevis_document_type(message: Message, state: FSMContext) -> None:
    if message.text == "🪪 کارت آمایش":
        await state.update_data(document_type="کارت آمایش")
        await state.set_state(KhodnevisForm.amayesh)
        await message.answer("۴/۷\n📸 عکس کارت آمایش را ارسال کنید.\nمثال: عکس واضح از تمام کارت.\nمحدودیت: فقط عکس، واضح و خوانا.", reply_markup=cancel_menu())
    elif message.text == "🛂 پاسپورت":
        await state.update_data(document_type="پاسپورت")
        await state.set_state(KhodnevisForm.passport_first)
        await message.answer("۴/۷\n📸 عکس صفحه اول پاسپورت را ارسال کنید.\nمثال: عکس واضح از صفحه مشخصات.\nمحدودیت: فقط عکس، واضح و خوانا؛ این صفحه الزامی است.", reply_markup=cancel_menu())
    else:
        await message.answer("یکی از دو گزینه را انتخاب کنید.", reply_markup=document_type_menu())


@router.message(KhodnevisForm.amayesh, F.photo)
async def khodnevis_amayesh(message: Message, state: FSMContext) -> None:
    await state.update_data(amayesh=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.own_mobile)
    await message.answer("شماره موبایل به نام خود شخص را وارد کنید:", reply_markup=cancel_menu())


@router.message(KhodnevisForm.passport_first, F.photo)
async def khodnevis_passport_first(message: Message, state: FSMContext) -> None:
    await state.update_data(passport_first=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.passport_renewal)
    await message.answer("صفحه تمدید پاسپورت را دارید؟", reply_markup=optional_document_menu())


@router.message(KhodnevisForm.passport_renewal)
async def khodnevis_passport_renewal(message: Message, state: FSMContext) -> None:
    if message.text == "⏭️ ندارم / رد کردن":
        await state.update_data(passport_renewal=None)
        await state.set_state(KhodnevisForm.residence_renewal)
        await message.answer("صفحه تمدید اقامت/ویزا را دارید؟", reply_markup=optional_document_menu())
    elif message.text == "📸 ارسال تصویر":
        await message.answer("📸 تصویر صفحه تمدید پاسپورت را ارسال کنید.\nمثال: عکس واضح از صفحه تمدید.\nمحدودیت: فقط عکس، واضح و خوانا.", reply_markup=cancel_menu())
    else:
        await message.answer("یکی از گزینه‌ها را انتخاب کنید.", reply_markup=optional_document_menu())


@router.message(KhodnevisForm.passport_renewal, F.photo)
async def khodnevis_passport_renewal_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(passport_renewal=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.residence_renewal)
    await message.answer("صفحه تمدید اقامت/ویزا را دارید؟", reply_markup=optional_document_menu())


@router.message(KhodnevisForm.residence_renewal)
async def khodnevis_residence_renewal(message: Message, state: FSMContext) -> None:
    if message.text == "⏭️ ندارم / رد کردن":
        await state.update_data(residence_renewal=None)
        await state.set_state(KhodnevisForm.own_mobile)
        await message.answer("شماره موبایل به نام خود شخص را وارد کنید:", reply_markup=cancel_menu())
    elif message.text == "📸 ارسال تصویر":
        await message.answer("📸 تصویر صفحه تمدید اقامت/ویزا را ارسال کنید.\nمثال: عکس واضح از صفحه تمدید.\nمحدودیت: فقط عکس، واضح و خوانا.", reply_markup=cancel_menu())
    else:
        await message.answer("یکی از گزینه‌ها را انتخاب کنید.", reply_markup=optional_document_menu())


@router.message(KhodnevisForm.residence_renewal, F.photo)
async def khodnevis_residence_renewal_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(residence_renewal=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.own_mobile)
    await message.answer("شماره موبایل به نام خود شخص را وارد کنید:", reply_markup=cancel_menu())


@router.message(KhodnevisForm.own_mobile)
async def khodnevis_own_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست.", reply_markup=cancel_menu())
        return
    await state.update_data(own_mobile=normalize_mobile(value))
    data = await state.get_data()
    await state.set_state(KhodnevisForm.confirm)
    await message.answer(
        "📋 خلاصه درخواست\n\n"
        f"نام: {data.get('full_name')}\n"
        f"موبایل در دسترس: {data.get('mobile')}\n"
        f"مدرک: {data.get('document_type')}\n"
        f"موبایل به نام شخص: {data.get('own_mobile')}\n\n"
        "اگر اطلاعات درست است «تأیید و ادامه» را بزنید.",
        reply_markup=confirm_menu(),
    )


@router.message(KhodnevisForm.confirm, F.text == "✅ تأیید و ادامه")
async def khodnevis_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await save_order_data(data)
    await show_payment_options(message, state, data["order_id"])


@router.message(KhodnevisForm.receipt, F.photo)
@router.message(KhodnevisForm.receipt, F.document)
async def khodnevis_receipt(message: Message, state: FSMContext) -> None:
    try:
        await save_receipt(message, state)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=cancel_menu())
        return
    await state.clear()
    await message.answer("✅ رسید ثبت شد و در انتظار بررسی است.", reply_markup=await user_main_menu(message.from_user.id))


async def save_order_data(data: dict) -> None:
    order_id = data["order_id"]
    excluded = {"order_id", "public_id", "service_code", "pending_companion_name", "companions"}
    payload = {k: v for k, v in data.items() if k not in excluded}
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            raise ValueError("درخواست پیدا نشد.")
        order.data_json = json.dumps(payload, ensure_ascii=False)
        order.status = "waiting_payment"
        await session.execute(delete(Companion).where(Companion.order_id == order.id))
        await session.execute(delete(Document).where(Document.order_id == order.id))
        session.add_all(
            Companion(order_id=order.id, full_name=x["full_name"], mobile=x["mobile"])
            for x in data.get("companions", [])
        )
        document_map = {
            "identity_document": f"مدرک شناسایی ({data.get('identity_document_type') or 'سایر'})",
            "tazkira": "تذکره",
            "amayesh": "کارت آمایش",
            "passport_first": "صفحه اول پاسپورت",
            "passport_renewal": "تمدید پاسپورت",
            "residence_renewal": "تمدید اقامت/ویزا",
        }
        for key, label in document_map.items():
            file_id = data.get(key)
            if file_id:
                session.add(Document(order_id=order.id, document_type=label, telegram_file_id=file_id))
        await session.commit()


async def save_receipt(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        raise ValueError("درخواست پرداخت پیدا نشد. لطفاً دوباره از منوی اصلی شروع کنید.")
    if not message.photo and not message.document:
        raise ValueError("لطفاً رسید را به صورت عکس یا فایل ارسال کنید.")

    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Order, Service)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(
                    Order.id == order_id,
                    User.telegram_id == message.from_user.id,
                )
            )
        ).one_or_none()
        if not row:
            raise ValueError("این درخواست متعلق به حساب شما نیست یا پیدا نشد.")

        order, service = row
        if order.status not in {"waiting_payment", "rejected"}:
            if order.status == "waiting_receipt_review":
                raise ValueError("رسید این درخواست قبلاً ثبت شده و در انتظار بررسی است.")
            if order.status == "payment_approved":
                raise ValueError("پرداخت این درخواست قبلاً تأیید شده است.")
            raise ValueError("این درخواست در حال حاضر امکان دریافت رسید ندارد.")

        await session.execute(
            update(Payment)
            .where(Payment.order_id == order.id, Payment.status == "pending")
            .values(status="superseded")
        )
        payload = json.loads(order.data_json or "{}")
        base_amount = int(order.price_snapshot_toman or service.price_toman)
        coupon = None
        coupon_code = payload.get("discount_code")
        if coupon_code:
            coupon = (await session.execute(
                select(DiscountCode).where(DiscountCode.code == coupon_code)
            )).scalar_one_or_none()
            if not coupon or not coupon.active or (
                coupon.expires_at and coupon.expires_at <= __import__("datetime").datetime.now()
            ) or (coupon.max_uses is not None and coupon.used_count >= coupon.max_uses):
                coupon = None
        final_amount = max(0, base_amount - calculate_discount(base_amount, coupon))
        session.add(
            Payment(
                order_id=order.id,
                amount_toman=final_amount,
                receipt_file_id=(message.photo[-1].file_id if message.photo else message.document.file_id),
                receipt_type=("photo" if message.photo else "document"),
                status="pending",
            )
        )
        order.status = "waiting_receipt_review"
        await session.commit()


@router.callback_query(F.data.startswith("retry_receipt:"))
async def retry_receipt_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Order, Service)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(Order.id == order_id, User.telegram_id == callback.from_user.id)
            )
        ).one_or_none()
    if not row or row[0].status != "rejected":
        await callback.answer("این درخواست برای ارسال مجدد رسید آماده نیست.", show_alert=True)
        return
    order, service = row
    async with SessionLocal() as session:
        latest_payment = (
            await session.execute(
                select(Payment)
                .where(Payment.order_id == order.id)
                .order_by(Payment.id.desc())
            )
        ).scalars().first()
    if latest_payment and latest_payment.status == "approved":
        await callback.answer("این درخواست قبلاً پرداخت تأییدشده دارد و امکان ارسال مجدد رسید ندارد.", show_alert=True)
        return
    await state.clear()
    await state.update_data(order_id=order.id, public_id=order.public_id, service_code=service.code)
    await state.set_state(RetryReceiptForm.receipt)
    await callback.answer()
    await callback.message.answer(
        f"🧾 ارسال مجدد رسید {order.public_id}\n"
        f"مبلغ: {(order.price_snapshot_toman or service.price_toman):,} تومان\n"
        "لطفاً تصویر رسید جدید را ارسال کنید.",
        reply_markup=cancel_menu(),
    )


@router.message(RetryReceiptForm.receipt, F.photo)
@router.message(RetryReceiptForm.receipt, F.document)
async def retry_receipt_save(message: Message, state: FSMContext) -> None:
    try:
        await save_receipt(message, state)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=cancel_menu())
        return
    await state.clear()
    await message.answer("✅ رسید جدید ثبت شد و دوباره برای بررسی ارسال گردید.", reply_markup=await user_main_menu(message.from_user.id))


@router.message(F.text == "📋 پیگیری درخواست‌ها")
async def track_orders(message: Message, telegram_id: int | None = None) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Order, Service)
            .join(Service, Service.id == Order.service_id)
            .join(User, User.id == Order.user_id)
            .where(
                User.telegram_id == (telegram_id or message.from_user.id),
                Order.status.notin_(["draft", "waiting_payment"]),
            )
            .order_by(Order.id.desc())
        )
        rows = result.all()
    if not rows:
        await message.answer("هنوز درخواستی ثبت نکرده‌اید.", reply_markup=await user_main_menu(telegram_id or message.from_user.id))
        return
    text = "📋 درخواست‌های شما:\n\n"
    for order, service in rows:
        text += f"{order.public_id} — {service.name}\nوضعیت: {STATUS_TEXT.get(order.status, order.status)}\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [ui_button(
            text=f"🔎 {order.public_id} | {STATUS_TEXT.get(order.status, order.status)}",
            callback_data=f"user:order:{order.id}",
        )]
        for order, service in rows[:20]
    ])
    await message.answer(text, reply_markup=keyboard)



@router.callback_query(F.data.startswith("user:order:"))
async def user_order_detail(callback: CallbackQuery) -> None:
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Order, Service, User)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(Order.id == order_id, User.telegram_id == callback.from_user.id)
            )
        ).one_or_none()
        if not row:
            await callback.answer("این درخواست متعلق به شما نیست.", show_alert=True)
            return
        order, service, user = row
        data = json.loads(order.data_json or "{}")
        companions = (await session.execute(
            select(Companion).where(Companion.order_id == order.id).order_by(Companion.id)
        )).scalars().all()
        documents = (await session.execute(
            select(Document).where(Document.order_id == order.id).order_by(Document.id)
        )).scalars().all()
    text = (
        f"📋 درخواست {order.public_id}\n\n"
        f"🧾 خدمت: {service.name}\n"
        f"📌 وضعیت: {STATUS_TEXT.get(order.status, order.status)}\n"
        f"💰 مبلغ ثبت‌شده: {(order.price_snapshot_toman or service.price_toman):,} تومان\n"
        f"📅 تاریخ ثبت: {order.created_at.strftime('%Y/%m/%d') if order.created_at else '—'}\n"
        f"👤 نام: {data.get('full_name') or '—'}\n"
        f"📱 موبایل: {data.get('mobile') or '—'}\n"
    )
    for key, label in (
        ("birth_date_gregorian", "تاریخ تولد"),
        ("return_date_gregorian", "آخرین بازگشت به افغانستان"),
        ("consulate", "کنسولگری"),
        ("document_type", "نوع مدرک"),
        ("own_mobile", "موبایل به نام شخص"),
    ):
        if data.get(key):
            text += f"{label}: {data[key]}\n"
    text += "\n👨‍👩‍👧 همراهان:\n" + (
        "\n".join(f"• {x.full_name} — {x.mobile}" for x in companions) if companions else "ندارد"
    )
    text += "\n\n📎 مدارک ثبت‌شده: " + (
        ", ".join(d.document_type for d in documents) if documents else "ندارد"
    )
    buttons = []
    if order.status == "rejected":
        buttons.append([ui_button(text="🧾 ارسال مجدد رسید", callback_data=f"retry_receipt:{order.id}")])
    buttons.append([ui_button(text="📞 پشتیبانی", callback_data=f"user:support:{order.id}")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    for doc in documents:
        try:
            await callback.message.answer_photo(doc.telegram_file_id, caption=f"📎 {doc.document_type} | {order.public_id}")
        except Exception:
            await callback.message.answer(f"⚠️ تصویر «{doc.document_type}» قابل نمایش مجدد نیست.")
    await callback.answer()




@router.callback_query(F.data == "pay:wallet")
async def pay_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await callback.answer("درخواست پرداخت پیدا نشد.", show_alert=True)
        return
    try:
        ok = await apply_wallet_payment(callback.from_user.id, order_id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    if not ok:
        credit = await get_wallet_balance(callback.from_user.id)
        await callback.answer("اعتبار کافی نیست؛ کارت به کارت را انتخاب کنید.", show_alert=True)
        try:
            await callback.message.edit_text(
                f"💰 اعتبار شما: {credit:,} تومان\n\nاعتبار کافی نیست. لطفاً روش کارت به کارت را انتخاب کنید.",
                reply_markup=payment_choice_menu(credit),
            )
        except Exception as exc:
            # Clicking the same wallet button again can produce an identical message;
            # Telegram rejects that no-op edit. Do not let it become a failed update.
            if "message is not modified" not in str(exc).lower():
                raise
            await callback.answer("اعتبار کافی نیست؛ کارت به کارت را انتخاب کنید.", show_alert=True)
        return
    await state.clear()
    await callback.answer("پرداخت از اعتبار انجام شد.")
    await callback.message.edit_text("✅ پرداخت با اعتبار با موفقیت انجام شد.\n\nمبلغ فقط یک‌بار از اعتبار شما کسر شد و پرونده برای اپراتورهای مجاز ارسال می‌شود.", reply_markup=await user_main_menu(callback.from_user.id))
    # import محلی از وابستگی دوری هنگام بارگذاری ماژول‌ها جلوگیری می‌کند.
    from app.bot.admin import send_case_to_operator
    await send_case_to_operator(callback.bot, order_id)
    for admin_id in get_settings().admin_id_set:
        try:
            await callback.bot.send_message(admin_id, f"💰 پرداخت با اعتبار تأیید شد.\nشماره درخواست: {order_id}")
        except Exception:
            pass


@router.callback_query(F.data == "pay:card")
async def pay_card(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await callback.answer("درخواست پرداخت پیدا نشد.", show_alert=True)
        return
    await state.set_state(IdentityForm.receipt if data.get("service_code") == ServiceCode.IDENTITY.value else KhodnevisForm.receipt)
    await callback.answer()
    invoice_text = await payment_instructions(order_id)
    async with SessionLocal() as session:
        card_setting = (await session.execute(select(Setting).where(Setting.key == "card_number"))).scalar_one_or_none()
    card_number = card_setting.value if card_setting and card_setting.value else "تنظیم نشده"
    amount_toman, _, _ = await order_amount_and_coupon(order_id)
    await callback.message.edit_text(
        invoice_text,
        reply_markup=payment_invoice_menu(card_number, amount_toman * 10),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "pay:coupon")
async def pay_coupon(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PaymentForm.coupon)
    await callback.answer()
    await callback.message.edit_text("🏷️ کد تخفیف را وارد کنید.\nمثال: RENA20", reply_markup=cancel_menu())


@router.message(PaymentForm.coupon)
async def payment_coupon(message: Message, state: FSMContext) -> None:
    code = (message.text or "").strip().upper()
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id or not code:
        await message.answer("❌ کد تخفیف معتبر نیست.", reply_markup=cancel_menu())
        return
    async with SessionLocal() as session:
        coupon = (await session.execute(select(DiscountCode).where(DiscountCode.code == code))).scalar_one_or_none()
        if not coupon or not coupon.active:
            await message.answer("❌ این کد تخفیف معتبر یا فعال نیست.", reply_markup=cancel_menu())
            return
        if coupon.expires_at and coupon.expires_at <= __import__("datetime").datetime.now():
            await message.answer("❌ مهلت این کد تخفیف تمام شده است.", reply_markup=cancel_menu())
            return
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            await message.answer("❌ ظرفیت استفاده از این کد تخفیف تکمیل شده است.", reply_markup=cancel_menu())
            return
        order = await session.get(Order, order_id)
        if not order:
            await message.answer("❌ درخواست پیدا نشد.", reply_markup=cancel_menu())
            return
        payload = json.loads(order.data_json or "{}")
        payload["discount_code"] = code
        order.data_json = json.dumps(payload, ensure_ascii=False)
        await session.commit()
    await show_payment_options(message, state, order_id)


@router.callback_query(F.data == "menu:wallet")
async def wallet_account(callback: CallbackQuery) -> None:
    await callback.answer()
    balance = await get_wallet_balance(callback.from_user.id)
    await callback.message.edit_text(
        f"💰 اعتبار شما\n\nموجودی فعلی: {balance:,} تومان",
        reply_markup=wallet_menu(balance),
    )


@router.callback_query(F.data == "wallet:topup")
async def wallet_topup_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WalletTopupForm.amount)
    await callback.answer()
    await callback.message.edit_text(
        "➕ افزایش اعتبار\n\nمبلغ موردنظر را به تومان وارد کنید.\nمبلغ افزایش اعتبار باید بیشتر از ۲۰,۰۰۰ تومان باشد\nمثال: ۵۰,۰۰۰",
        reply_markup=cancel_menu(),
    )


@router.message(WalletTopupForm.amount)
async def wallet_topup_amount(message: Message, state: FSMContext) -> None:
    raw = normalize_digits(message.text or "").replace(",", "").replace("٬", "").strip()
    if not raw.isdigit() or int(raw) <= 20000:
        await message.answer("❌ مبلغ باید بیشتر از ۲۰,۰۰۰ تومان باشد.\nمثال: ۵۰,۰۰۰", reply_markup=cancel_menu())
        return
    amount = int(raw)
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one()
        topup = WalletTopup(user_id=user.id, amount_toman=amount)
        session.add(topup)
        await session.flush()
        await state.update_data(topup_id=topup.id)
        await session.commit()
    await state.set_state(WalletTopupForm.receipt)
    invoice_text = await wallet_topup_invoice(amount)
    async with SessionLocal() as session:
        card_setting = (await session.execute(select(Setting).where(Setting.key == "card_number"))).scalar_one_or_none()
    card_number = card_setting.value if card_setting and card_setting.value else "تنظیم نشده"
    await message.answer(
        invoice_text,
        reply_markup=payment_invoice_menu(card_number, amount * 10),
        parse_mode=ParseMode.HTML,
    )


async def wallet_topup_invoice(amount: int) -> str:
    async with SessionLocal() as session:
        number = (await session.execute(select(Setting).where(Setting.key == "card_number"))).scalar_one_or_none()
        holder = (await session.execute(select(Setting).where(Setting.key == "card_holder"))).scalar_one_or_none()
    card_number = number.value if number and number.value else "تنظیم نشده"
    card_holder = holder.value if holder and holder.value else "تنظیم نشده"
    return (f"🧾 فاکتور افزایش اعتبار\n━━━━━━━━━━━━━━\nمبلغ: <code>{amount:,}</code> تومان\nریال: <code>{amount*10}</code>\n"
            f"💳 شماره کارت: <code>{card_number}</code>\n"
            f"👤 به نام: {card_holder}\n"
            "━━━━━━━━━━━━━━\n📸 رسید واریز را به صورت عکس یا فایل ارسال کنید.")


@router.message(WalletTopupForm.receipt, F.photo)
@router.message(WalletTopupForm.receipt, F.document)
async def wallet_topup_receipt(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    topup_id = data.get("topup_id")
    if not topup_id:
        await message.answer("❌ درخواست افزایش اعتبار پیدا نشد.", reply_markup=cancel_menu())
        return

    async with SessionLocal() as session:
        topup = await session.get(WalletTopup, topup_id)
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()
        if (
            not topup or not user or topup.user_id != user.id
            or topup.status != "waiting_receipt_review"
        ):
            await message.answer(
                "❌ این درخواست افزایش اعتبار قابل ثبت نیست.",
                reply_markup=cancel_menu(),
            )
            return
        topup.receipt_file_id = message.photo[-1].file_id if message.photo else message.document.file_id
        topup.receipt_type = "photo" if message.photo else "document"
        amount = topup.amount_toman
        await session.commit()

    await state.clear()
    notification = (
        f"🔔 رسید جدید افزایش اعتبار\n"
        f"🧾 شماره شارژ: #{topup_id}\n"
        f"👤 مشترک: {user.first_name or ''} {user.last_name or ''}\n"
        f"🆔 شناسه تلگرام: {user.telegram_id}\n"
        f"💰 مبلغ: {amount:,} تومان\n"
        f"📌 وضعیت: در انتظار بررسی"
    )
    for admin_id in get_settings().admin_id_set:
        try:
            await message.bot.send_message(
                admin_id,
                notification,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🔎 بررسی رسید شارژ",
                        callback_data=f"adm:topup:view:{topup_id}",
                        style="primary",
                    )
                ]]),
            )
            await message.copy_to(admin_id)
        except Exception:
            # The user's receipt remains saved even if an administrator cannot be reached.
            continue

    await message.answer(
        "✅ رسید افزایش اعتبار ثبت شد و برای مدیریت ارسال شد.",
        reply_markup=await user_main_menu(message.from_user.id),
    )

@router.message(WalletTopupForm.receipt)
async def wallet_topup_receipt_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("🧾 لطفاً رسید را به صورت عکس یا فایل ارسال کنید.", reply_markup=cancel_menu())


@router.callback_query(F.data == "wallet:history")
async def wallet_history(callback: CallbackQuery) -> None:
    await callback.answer()
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == callback.from_user.id))).scalar_one_or_none()
        if not user:
            await callback.answer("حساب پیدا نشد.", show_alert=True); return
        rows = (await session.execute(select(WalletTransaction).where(WalletTransaction.user_id == user.id).order_by(WalletTransaction.created_at.desc()).limit(30))).scalars().all()
    if not rows:
        text = "📜 هنوز تراکنشی برای اعتبار شما ثبت نشده است."
    else:
        text = "📜 تاریخچه اعتبار\n\n" + "\n".join(
            f"{'➕' if x.amount_toman > 0 else '➖'} {abs(x.amount_toman):,} تومان | {x.description}"
            for x in rows
        )
    await callback.message.edit_text(text, reply_markup=wallet_menu(await get_wallet_balance(callback.from_user.id)))


@router.message(F.text == "👤 حساب من")
async def account(message: Message, telegram_id: int | None = None) -> None:
    user = await get_or_create_user(message, telegram_id=telegram_id)
    await message.answer(
        f"👤 حساب شما\nشناسه تلگرام: {user.telegram_id}\n"
        f"نام: {user.first_name or ''} {user.last_name or ''}".strip(),
        reply_markup=await user_main_menu(telegram_id or message.from_user.id),
    )



@router.callback_query(F.data.startswith("user:support:"))
async def user_support_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Order, Service, User)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(
                    Order.id == order_id,
                    User.telegram_id == callback.from_user.id,
                    Order.status.not_in(["draft", "waiting_payment"]),
                )
            )
        ).one_or_none()
        if not row:
            await callback.answer("این درخواست فعلاً قابل پشتیبانی نیست.", show_alert=True)
            return
        order, service, user = row
        ticket = (
            await session.execute(select(Ticket).where(Ticket.order_id == order.id))
        ).scalar_one_or_none()
        if ticket is None:
            ticket = Ticket(order_id=order.id, status="open")
            session.add(ticket)
        elif ticket.status != "open":
            ticket.status = "open"
        await session.commit()
    await state.clear()
    await state.update_data(support_order_id=order_id)
    await state.set_state(SupportForm.message)
    await callback.answer()
    await callback.message.answer(
        f"📞 پشتیبانی درخواست {order.public_id}\n\n"
        "پیام، عکس، فایل، ویدیو یا صوت خود را ارسال کنید.\n"
        "پیام شما مستقیم برای مدیریت و اپراتورهای مجاز ارسال می‌شود.",
        reply_markup=cancel_menu(),
    )


@router.message(SupportForm.message)
async def user_support_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("support_order_id")
    if not order_id:
        await state.clear()
        await start(message, state)
        return
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(Ticket, Order, Service)
                .join(Order, Ticket.order_id == Order.id)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(
                    Order.id == order_id,
                    User.telegram_id == message.from_user.id,
                )
            )
        ).one_or_none()
        if not row:
            await state.clear()
            await message.answer("❌ درخواست پشتیبانی پیدا نشد.", reply_markup=await user_main_menu(message.from_user.id))
            return
        ticket, order, service = row

        # اگر تیکت در فاصله بین انتخاب درخواست و ارسال پیام بسته شده باشد،
        # با ارسال پیام مشترک دوباره فعال می‌شود؛ پیام مشترک نباید به خاطر
        # وضعیت لحظه‌ای تیکت از بین برود.
        if ticket.status != "open":
            ticket.status = "open"
            await session.flush()
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
        session.add(TicketMessage(
            ticket_id=ticket.id,
            sender_type="user",
            sender_telegram_id=message.from_user.id,
            content_type=message.content_type,
            text=message.text or message.caption,
            file_id=file_id,
        ))
        await session.commit()
    recipients = set(get_settings().admin_id_set)
    support_id = get_settings().support_telegram_id
    if support_id:
        recipients.add(support_id)
    async with SessionLocal() as session:
        operators = (await session.execute(select(Operator).where(Operator.active.is_(True)))).scalars().all()
    for op in operators:
        try:
            permissions = json.loads(op.permissions_json or "{}")
        except (TypeError, json.JSONDecodeError):
            permissions = {}
        if permissions.get("view_orders") and permissions.get("message_user"):
            recipients.add(op.telegram_id)
    sent_any = False
    for recipient_id in recipients:
        try:
            # ابتدا نوتیفیکیشن مستقل ارسال می‌شود تا دریافت پیام تیکت برای پشتیبان/اپراتور قطعی و قابل مشاهده باشد.
            await message.bot.send_message(
                recipient_id,
                f"🔔 پیام جدید تیکت پشتیبانی\n📋 درخواست: {order.public_id}\n🪪 خدمت: {service.name}\n\n"
                "مشترک پیام جدیدی برای شما ارسال کرده است.",
            )
            await message.copy_to(recipient_id)
            sent_any = True
        except Exception:
            continue
    await state.clear()
    if sent_any:
        await message.answer("✅ پیام شما برای پشتیبانی ارسال شد.", reply_markup=await user_main_menu(message.from_user.id))
    else:
        await message.answer("⚠️ پیام ثبت شد، اما ارسال به پشتیبان در دسترس نبود. مدیریت باید شناسه عددی پشتیبان را در تنظیمات بات ثبت کند.", reply_markup=await user_main_menu(message.from_user.id))

@router.message(F.text == "📞 پشتیبانی")
async def support(message: Message, telegram_id: int | None = None, show_direct: bool = True) -> None:
    uid = telegram_id or message.from_user.id
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(Order, Service)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(
                User.telegram_id == uid,
                Order.status.in_(["payment_approved", "in_progress", "waiting_user"]),
            )
            .order_by(Order.id.desc())
            .limit(20)
        )).all()
        for order, service in rows:
            ticket = (
                await session.execute(select(Ticket).where(Ticket.order_id == order.id))
            ).scalar_one_or_none()
            if ticket is None:
                session.add(Ticket(order_id=order.id, status="open"))
            elif ticket.status != "open":
                ticket.status = "open"
        await session.commit()
    if show_direct:
        if rows:
            text = (
                "📞 پشتیبانی\n\n"
                "برای ارتباط مستقیم با پشتیبانی از دکمه زیر استفاده کنید.\n"
                "برای پیگیری یکی از درخواست‌های فعال نیز می‌توانید گزینه مربوط به آن را انتخاب کنید."
            )
            markup = support_menu(True)
        else:
            text = (
                "📞 پشتیبانی\n\n"
                "در حال حاضر درخواست فعال و قابل پشتیبانی ندارید.\n\n"
                "با این حال، برای راهنمایی و ارتباط مستقیم می‌توانید با پشتیبانی در ارتباط باشید."
            )
            markup = support_menu(False)
        await message.answer(text, reply_markup=markup)
    else:
        if not rows:
            await message.answer(
                "📞 پشتیبانی\n\nدر حال حاضر درخواست فعال و قابل پشتیبانی ندارید.",
                reply_markup=await user_main_menu(uid),
            )
            return
        buttons = [
            [ui_button(text=f"📞 {order.public_id} | {service.name}", callback_data=f"user:support:{order.id}")]
            for order, service in rows
        ]
        buttons.append([ui_button(text="❌ انصراف", callback_data="flow:cancel")])
        await message.answer("📞 درخواست موردنظر برای پشتیبانی را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# راهنمایی برای ورودی‌های نامعتبر در مراحل دریافت تصویر و رسید
@router.message(IdentityForm.identity_document)
async def identity_document_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر مدرک شناسایی را به صورت عکس ارسال کنید.", reply_markup=cancel_menu())


@router.message(IdentityForm.receipt)
async def identity_receipt_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("🧾 لطفاً تصویر رسید را به صورت عکس یا فایل ارسال کنید.", reply_markup=cancel_menu())


@router.message(IdentityForm.tazkira)
async def identity_tazkira_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر تذکره را به صورت عکس ارسال کنید.", reply_markup=cancel_menu())


@router.message(KhodnevisForm.amayesh)
async def khodnevis_amayesh_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر کارت آمایش را به صورت عکس ارسال کنید.", reply_markup=cancel_menu())


@router.message(KhodnevisForm.passport_first)
async def khodnevis_passport_first_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر صفحه اول پاسپورت را به صورت عکس ارسال کنید.", reply_markup=cancel_menu())


@router.message(KhodnevisForm.receipt)
async def khodnevis_receipt_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("🧾 لطفاً تصویر رسید را به صورت عکس یا فایل ارسال کنید.", reply_markup=cancel_menu())


@router.message(RetryReceiptForm.receipt)
async def retry_receipt_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("🧾 لطفاً تصویر رسید را به صورت عکس یا فایل ارسال کنید.", reply_markup=cancel_menu())
