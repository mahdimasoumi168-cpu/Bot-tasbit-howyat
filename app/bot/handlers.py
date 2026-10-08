import json
import re

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import delete, select, update

from app.bot.keyboards import (
    consulate_menu,
    document_type_menu,
    main_menu,
    optional_document_menu,
    yes_no_menu,
    single_action_menu,
    confirm_menu,
)
from app.bot.states import IdentityForm, KhodnevisForm, RetryReceiptForm, SupportForm
from app.core.config import get_settings
from app.db.models import Companion, Document, Operator, Order, Payment, Service, ServiceCode, Setting, Ticket, TicketMessage, User
from app.db.session import SessionLocal
from app.utils.dates import gregorian_display, jalali_to_gregorian
from app.utils.ids import public_order_id

router = Router()

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


def valid_mobile(value: str) -> bool:
    digits = re.sub(r"[^0-9۰-۹]", "", value.strip()).translate(
        str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    )
    return bool(re.fullmatch(r"(?:09\d{9}|9\d{9}|989\d{9}|00989\d{9})", digits))


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
    return (
        "💳 پرداخت کارت‌به‌کارت\n\n"
        f"مبلغ: {(order.price_snapshot_toman or service.price_toman):,} تومان\n"
        f"شماره کارت: {card_number}\n"
        f"به نام: {card_holder}\n\n"
        "پس از واریز، تصویر رسید را ارسال کنید."
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, telegram_id: int | None = None) -> None:
    uid = telegram_id or message.from_user.id
    await state.clear()
    await get_or_create_user(message, telegram_id=telegram_id)
    await message.answer(
        "سلام 🌷\nبه «رنا یار بات» خوش آمدید.\n\nخدمت موردنظر را انتخاب کنید:",
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
    await support(callback.message, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "identity:consulate:z")
async def inline_consulate_z(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.consulate:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(consulate="🇦🇫 زاهدان"); await state.set_state(IdentityForm.identity_document)
    await callback.message.edit_text("۶/۸\n📸 تصویر مدرک شناسایی را ارسال کنید.", reply_markup=single_action_menu())

@router.callback_query(F.data == "identity:consulate:m")
async def inline_consulate_m(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.consulate:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(consulate="🇦🇫 مشهد"); await state.set_state(IdentityForm.identity_document)
    await callback.message.edit_text("۶/۸\n📸 تصویر مدرک شناسایی را ارسال کنید.", reply_markup=single_action_menu())

@router.callback_query(F.data == "identity:companion:y")
async def inline_companion_yes(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != IdentityForm.companion_choice:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.set_state(IdentityForm.companion_name)
    await callback.message.edit_text("✍️ نام و نام خانوادگی همراه را وارد کنید.", reply_markup=single_action_menu())

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
    await callback.message.edit_text("۴/۷\n📸 تصویر کارت آمایش را ارسال کنید.", reply_markup=single_action_menu())

@router.callback_query(F.data == "khodnevis:doc:passport")
async def inline_doc_passport(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() != KhodnevisForm.document_type:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer(); await state.update_data(document_type="پاسپورت"); await state.set_state(KhodnevisForm.passport_first)
    await callback.message.edit_text("۴/۷\n📸 تصویر صفحه اول پاسپورت الزامی است.", reply_markup=single_action_menu())

@router.callback_query(F.data.startswith("khodnevis:optional:"))
async def inline_optional_document(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state(); action = callback.data.rsplit(":", 1)[1]
    if current not in {KhodnevisForm.passport_renewal, KhodnevisForm.residence_renewal}:
        await callback.answer("این گزینه دیگر فعال نیست.", show_alert=True); return
    await callback.answer()
    if action == "send":
        target = "صفحه تمدید پاسپورت" if current == KhodnevisForm.passport_renewal else "صفحه تمدید اقامت/ویزا"
        await callback.message.edit_text(f"📸 تصویر {target} را ارسال کنید.", reply_markup=single_action_menu()); return
    if current == KhodnevisForm.passport_renewal:
        await state.update_data(passport_renewal=None); await state.set_state(KhodnevisForm.residence_renewal)
        await callback.message.edit_text("صفحه تمدید اقامت/ویزا را دارید؟", reply_markup=optional_document_menu())
    else:
        await state.update_data(residence_renewal=None); await state.set_state(KhodnevisForm.own_mobile)
        await callback.message.edit_text("📱 شماره موبایل به نام خود شخص را ارسال کنید.", reply_markup=single_action_menu())

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
        order_id=order.id, public_id=order.public_id, service_code=ServiceCode.IDENTITY.value
    )
    await state.set_state(IdentityForm.full_name)
    await message.answer("۱/۸\nنام و نام خانوادگی را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.full_name)
async def identity_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 3:
        await message.answer("❌ نام و نام خانوادگی را کامل وارد کنید.")
        return
    await state.update_data(full_name=value)
    await state.set_state(IdentityForm.mobile)
    await message.answer("۲/۸\nشماره موبایل در دسترس را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.mobile)
async def identity_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست. مثال: 09123456789")
        return
    await state.update_data(mobile=value)
    await state.set_state(IdentityForm.birth_date)
    await message.answer("۳/۸\nتاریخ تولد را به شمسی وارد کنید. مثال: ۱۴۰۵/۰۱/۱۵", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.birth_date)
async def identity_birth(message: Message, state: FSMContext) -> None:
    try:
        value = jalali_to_gregorian(message.text or "")
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return
    await state.update_data(birth_date_gregorian=gregorian_display(value))
    await state.set_state(IdentityForm.return_date)
    await message.answer("۴/۸\nآخرین تاریخ بازگشت به افغانستان را به شمسی وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.return_date)
async def identity_return(message: Message, state: FSMContext) -> None:
    try:
        value = jalali_to_gregorian(message.text or "")
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
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
    await state.set_state(IdentityForm.identity_document)
    await message.answer("۶/۸\nعکس مدرک شناسایی را ارسال کنید.", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.identity_document, F.photo)
async def identity_document(message: Message, state: FSMContext) -> None:
    await state.update_data(identity_document=message.photo[-1].file_id)
    await state.set_state(IdentityForm.tazkira)
    await message.answer("۷/۸\nعکس تذکره را ارسال کنید.", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.tazkira, F.photo)
async def identity_tazkira(message: Message, state: FSMContext) -> None:
    await state.update_data(tazkira=message.photo[-1].file_id)
    await state.set_state(IdentityForm.companion_choice)
    await message.answer("۸/۸\nآیا همراه دیگری دارید؟", reply_markup=yes_no_menu())


@router.message(IdentityForm.companion_choice)
async def identity_companion_choice(message: Message, state: FSMContext) -> None:
    if message.text == "✅ بله":
        await state.set_state(IdentityForm.companion_name)
        await message.answer("نام و نام خانوادگی همراه را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))
    elif message.text == "❌ خیر":
        await show_identity_summary(message, state)
    else:
        await message.answer("لطفاً «بله» یا «خیر» را انتخاب کنید.", reply_markup=yes_no_menu())


@router.message(IdentityForm.companion_name)
async def identity_companion_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 3:
        await message.answer("❌ نام همراه را کامل وارد کنید.")
        return
    await state.update_data(pending_companion_name=value)
    await state.set_state(IdentityForm.companion_mobile)
    await message.answer("شماره موبایل همراه را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(IdentityForm.companion_mobile)
async def identity_companion_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست.")
        return
    data = await state.get_data()
    companions = data.get("companions", [])
    companions.append({"full_name": data["pending_companion_name"], "mobile": value})
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
    await state.set_state(IdentityForm.receipt)
    await message.answer(await payment_instructions(data["order_id"]))


@router.message(IdentityForm.receipt, F.photo)
async def identity_receipt(message: Message, state: FSMContext) -> None:
    await save_receipt(message, state)
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
        order_id=order.id, public_id=order.public_id, service_code=ServiceCode.KHODNEVIS.value
    )
    await state.set_state(KhodnevisForm.full_name)
    await message.answer("۱/۷\nنام و نام خانوادگی را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(KhodnevisForm.full_name)
async def khodnevis_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 3:
        await message.answer("❌ نام و نام خانوادگی را کامل وارد کنید.")
        return
    await state.update_data(full_name=value)
    await state.set_state(KhodnevisForm.mobile)
    await message.answer("۲/۷\nشماره موبایل در دسترس را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(KhodnevisForm.mobile)
async def khodnevis_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست. مثال: 09123456789")
        return
    await state.update_data(mobile=value)
    await state.set_state(KhodnevisForm.document_type)
    await message.answer("۳/۷\nمدرک را انتخاب کنید:", reply_markup=document_type_menu())


@router.message(KhodnevisForm.document_type)
async def khodnevis_document_type(message: Message, state: FSMContext) -> None:
    if message.text == "🪪 کارت آمایش":
        await state.update_data(document_type="کارت آمایش")
        await state.set_state(KhodnevisForm.amayesh)
        await message.answer("۴/۷\nعکس کارت آمایش را ارسال کنید.", reply_markup=single_action_menu("🔄 شروع مجدد"))
    elif message.text == "🛂 پاسپورت":
        await state.update_data(document_type="پاسپورت")
        await state.set_state(KhodnevisForm.passport_first)
        await message.answer("۴/۷\nعکس صفحه اول پاسپورت الزامی است.", reply_markup=single_action_menu("🔄 شروع مجدد"))
    else:
        await message.answer("یکی از دو گزینه را انتخاب کنید.", reply_markup=document_type_menu())


@router.message(KhodnevisForm.amayesh, F.photo)
async def khodnevis_amayesh(message: Message, state: FSMContext) -> None:
    await state.update_data(amayesh=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.own_mobile)
    await message.answer("شماره موبایل به نام خود شخص را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


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
        await message.answer("حالا تصویر صفحه تمدید پاسپورت را ارسال کنید.", reply_markup=single_action_menu("🔄 شروع مجدد"))
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
        await message.answer("شماره موبایل به نام خود شخص را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))
    elif message.text == "📸 ارسال تصویر":
        await message.answer("حالا تصویر صفحه تمدید اقامت/ویزا را ارسال کنید.", reply_markup=single_action_menu("🔄 شروع مجدد"))
    else:
        await message.answer("یکی از گزینه‌ها را انتخاب کنید.", reply_markup=optional_document_menu())


@router.message(KhodnevisForm.residence_renewal, F.photo)
async def khodnevis_residence_renewal_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(residence_renewal=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.own_mobile)
    await message.answer("شماره موبایل به نام خود شخص را وارد کنید:", reply_markup=single_action_menu("🔄 شروع مجدد"))


@router.message(KhodnevisForm.own_mobile)
async def khodnevis_own_mobile(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not valid_mobile(value):
        await message.answer("❌ شماره موبایل معتبر نیست.")
        return
    await state.update_data(own_mobile=value)
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
    await state.set_state(KhodnevisForm.receipt)
    await message.answer(await payment_instructions(data["order_id"]))


@router.message(KhodnevisForm.receipt, F.photo)
async def khodnevis_receipt(message: Message, state: FSMContext) -> None:
    await save_receipt(message, state)
    await state.clear()
    await message.answer("✅ رسید ثبت شد و در انتظار بررسی است.", reply_markup=await user_main_menu(message.from_user.id))


async def save_order_data(data: dict) -> None:
    order_id = data["order_id"]
    excluded = {"order_id", "public_id", "service_code", "pending_companion_name", "companions"}
    payload = {k: v for k, v in data.items() if k not in excluded}
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            return
        order.data_json = json.dumps(payload, ensure_ascii=False)
        order.status = "waiting_payment"
        await session.execute(delete(Companion).where(Companion.order_id == order.id))
        await session.execute(delete(Document).where(Document.order_id == order.id))
        session.add_all(
            Companion(order_id=order.id, full_name=x["full_name"], mobile=x["mobile"])
            for x in data.get("companions", [])
        )
        document_map = {
            "identity_document": "مدرک شناسایی",
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
    async with SessionLocal() as session:
        order = await session.get(Order, data["order_id"])
        if order is None:
            return
        service = await session.get(Service, order.service_id)
        if service is None:
            return
        await session.execute(
            update(Payment)
            .where(Payment.order_id == order.id, Payment.status == "pending")
            .values(status="superseded")
        )
        session.add(
            Payment(
                order_id=order.id,
                amount_toman=order.price_snapshot_toman or service.price_toman,
                receipt_file_id=message.photo[-1].file_id,
                status="pending",
            )
        )
        order.status = "waiting_receipt_review"
        await session.commit()


@router.callback_query(F.data.startswith("retry_receipt:"))
async def retry_receipt_start(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.rsplit(":", 1)[1])
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
    await state.clear()
    await state.update_data(order_id=order.id, public_id=order.public_id, service_code=service.code)
    await state.set_state(RetryReceiptForm.receipt)
    await callback.answer()
    await callback.message.answer(
        f"🧾 ارسال مجدد رسید {order.public_id}\n"
        f"مبلغ: {(order.price_snapshot_toman or service.price_toman):,} تومان\n"
        "لطفاً تصویر رسید جدید را ارسال کنید."
    )


@router.message(RetryReceiptForm.receipt, F.photo)
async def retry_receipt_save(message: Message, state: FSMContext) -> None:
    await save_receipt(message, state)
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
        [InlineKeyboardButton(
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
        buttons.append([InlineKeyboardButton(text="🧾 ارسال مجدد رسید", callback_data=f"retry_receipt:{order.id}")])
    buttons.append([InlineKeyboardButton(text="📞 پشتیبانی", callback_data=f"user:support:{order.id}")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    for doc in documents:
        try:
            await callback.message.answer_photo(doc.telegram_file_id, caption=f"📎 {doc.document_type} | {order.public_id}")
        except Exception:
            await callback.message.answer(f"⚠️ تصویر «{doc.document_type}» قابل نمایش مجدد نیست.")
    await callback.answer()

@router.message(F.text == "👤 حساب من")
async def account(message: Message, telegram_id: int | None = None) -> None:
    user = await get_or_create_user(message, telegram_id=telegram_id)
    await message.answer(
        f"👤 حساب شما\nشناسه تلگرام: {user.telegram_id}\n"
        f"نام: {user.first_name or ''} {user.last_name or ''}".strip(),
        reply_markup=await user_main_menu(message.from_user.id),
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
                select(Ticket, Order, Service)
                .join(Order, Ticket.order_id == Order.id)
                .join(Service, Order.service_id == Service.id)
                .join(User, Order.user_id == User.id)
                .where(
                    Order.id == order_id,
                    User.telegram_id == callback.from_user.id,
                    Ticket.status == "open",
                )
            )
        ).one_or_none()
    if not row:
        await callback.answer("برای این درخواست هنوز گفت‌وگوی پشتیبانی فعال نیست.", show_alert=True)
        return
    await state.clear()
    await state.update_data(support_order_id=order_id)
    await state.set_state(SupportForm.message)
    await callback.answer()
    await callback.message.answer(
        f"📞 پشتیبانی درخواست {row[1].public_id}\n\n"
        "پیام، عکس، فایل، ویدیو یا صوت خود را ارسال کنید.\n"
        "پیام شما مستقیم برای مدیریت و اپراتورهای مجاز ارسال می‌شود.",
        reply_markup=single_action_menu("🔄 شروع مجدد"),
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
                    Ticket.status == "open",
                )
            )
        ).one_or_none()
        if not row:
            await state.clear()
            await message.answer("❌ گفت‌وگوی پشتیبانی فعال نیست.", reply_markup=await user_main_menu(message.from_user.id))
            return
        ticket, order, service = row
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
    async with SessionLocal() as session:
        operators = (await session.execute(select(Operator).where(Operator.active.is_(True)))).scalars().all()
    for op in operators:
        try:
            permissions = json.loads(op.permissions_json or "{}")
        except (TypeError, json.JSONDecodeError):
            permissions = {}
        if permissions.get("view_orders") and permissions.get("message_user"):
            recipients.add(op.telegram_id)
    for recipient_id in recipients:
        await message.bot.send_message(recipient_id, f"📞 پشتیبانی | {order.public_id} | {service.name}")
        await message.copy_to(recipient_id)
    await state.clear()
    await message.answer("✅ پیام شما برای پشتیبانی ارسال شد.", reply_markup=await user_main_menu(message.from_user.id))

@router.message(F.text == "📞 پشتیبانی")
async def support(message: Message, telegram_id: int | None = None) -> None:
    uid = telegram_id or message.from_user.id
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(Ticket, Order, Service)
            .join(Order, Ticket.order_id == Order.id)
            .join(Service, Order.service_id == Service.id)
            .join(User, Order.user_id == User.id)
            .where(User.telegram_id == uid, Ticket.status == "open")
            .order_by(Order.id.desc())
            .limit(20)
        )).all()
    if not rows:
        await message.answer(
            "📞 پشتیبانی\n\nبرای درخواست‌های فعال شما هنوز گفت‌وگوی پشتیبانی ایجاد نشده است.\nپس از تأیید پرداخت، امکان گفت‌وگو برای همان درخواست فعال می‌شود.",
            reply_markup=await user_main_menu(uid),
        )
        return
    buttons = [
        [InlineKeyboardButton(text=f"📞 {order.public_id} | {service.name}", callback_data=f"user:support:{order.id}")]
        for _, order, service in rows
    ]
    buttons.append([InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")])
    await message.answer("📞 درخواست موردنظر برای پشتیبانی را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# راهنمایی برای ورودی‌های نامعتبر در مراحل دریافت تصویر و رسید
@router.message(IdentityForm.identity_document)
async def identity_document_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر مدرک شناسایی را به صورت عکس ارسال کنید.", reply_markup=single_action_menu())


@router.message(IdentityForm.tazkira)
async def identity_tazkira_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر تذکره را به صورت عکس ارسال کنید.", reply_markup=single_action_menu())


@router.message(KhodnevisForm.amayesh)
async def khodnevis_amayesh_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر کارت آمایش را به صورت عکس ارسال کنید.", reply_markup=single_action_menu())


@router.message(KhodnevisForm.passport_first)
async def khodnevis_passport_first_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("📸 لطفاً تصویر صفحه اول پاسپورت را به صورت عکس ارسال کنید.", reply_markup=single_action_menu())


@router.message(KhodnevisForm.receipt)
async def khodnevis_receipt_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("🧾 لطفاً تصویر رسید پرداخت را به صورت عکس ارسال کنید.", reply_markup=single_action_menu())


@router.message(RetryReceiptForm.receipt)
async def retry_receipt_invalid(message: Message, state: FSMContext) -> None:
    await message.answer("🧾 لطفاً تصویر رسید جدید را به صورت عکس ارسال کنید.", reply_markup=single_action_menu())
