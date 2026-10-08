import json
import re

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
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
from app.bot.states import IdentityForm, KhodnevisForm, RetryReceiptForm
from app.core.config import get_settings
from app.db.models import Companion, Document, Operator, Order, Payment, Service, ServiceCode, Setting, User
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


async def get_or_create_user(message: Message) -> User:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            user.username = message.from_user.username
            await session.commit()
        return user


async def create_order(message: Message, service_code: ServiceCode) -> Order:
    await get_or_create_user(message)
    async with SessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == message.from_user.id))
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


async def payment_instructions(service_code: str) -> str:
    async with SessionLocal() as session:
        service = (
            await session.execute(select(Service).where(Service.code == service_code))
        ).scalar_one()
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
        f"مبلغ: {service.price_toman:,} تومان\n"
        f"شماره کارت: {card_number}\n"
        f"به نام: {card_holder}\n\n"
        "پس از واریز، تصویر رسید را ارسال کنید."
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await get_or_create_user(message)
    await message.answer(
        "سلام 🌷\nبه «رنا یار بات» خوش آمدید.\n\nخدمت موردنظر را انتخاب کنید:",
        reply_markup=await user_main_menu(message.from_user.id),
    )


@router.message(F.text == "🔄 شروع مجدد")
async def restart(message: Message, state: FSMContext) -> None:
    # «شروع مجدد» دقیقاً همان رفتار /start را اجرا می‌کند.
    await start(message, state)


@router.message(F.text == "🪪 تثبیت هویت")
async def identity_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        order = await create_order(message, ServiceCode.IDENTITY)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=await user_main_menu(message.from_user.id))
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
    await message.answer(await payment_instructions(ServiceCode.IDENTITY.value))


@router.message(IdentityForm.receipt, F.photo)
async def identity_receipt(message: Message, state: FSMContext) -> None:
    await save_receipt(message, state)
    await state.clear()
    await message.answer("✅ رسید شما ثبت شد و برای بررسی ارسال گردید.", reply_markup=await user_main_menu(message.from_user.id))


@router.message(F.text == "📝 کد رهگیری خودنویس")
async def khodnevis_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        order = await create_order(message, ServiceCode.KHODNEVIS)
    except ValueError as exc:
        await message.answer(f"❌ {exc}", reply_markup=await user_main_menu(message.from_user.id))
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
    await message.answer(await payment_instructions(ServiceCode.KHODNEVIS.value))


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
async def track_orders(message: Message) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Order, Service)
            .join(Service, Service.id == Order.service_id)
            .join(User, User.id == Order.user_id)
            .where(User.telegram_id == message.from_user.id)
            .order_by(Order.id.desc())
        )
        rows = result.all()
    if not rows:
        await message.answer("هنوز درخواستی ثبت نکرده‌اید.", reply_markup=await user_main_menu(message.from_user.id))
        return
    text = "📋 درخواست‌های شما:\n\n"
    for order, service in rows:
        text += f"{order.public_id} — {service.name}\nوضعیت: {STATUS_TEXT.get(order.status, order.status)}\n\n"
    await message.answer(text, reply_markup=await user_main_menu(message.from_user.id))


@router.message(F.text == "👤 حساب من")
async def account(message: Message) -> None:
    user = await get_or_create_user(message)
    await message.answer(
        f"👤 حساب شما\nشناسه تلگرام: {user.telegram_id}\n"
        f"نام: {user.first_name or ''} {user.last_name or ''}".strip(),
        reply_markup=await user_main_menu(message.from_user.id),
    )


@router.message(F.text == "📞 پشتیبانی")
async def support(message: Message) -> None:
    await message.answer(
        "📞 پشتیبانی\nپیام خود را ارسال کنید؛ اگر درخواست فعالی داشته باشید، برای مدیریت همان درخواست ارسال می‌شود.",
        reply_markup=await user_main_menu(message.from_user.id),
    )

