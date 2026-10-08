import json
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.bot.keyboards import (
    consulate_menu,
    document_type_menu,
    main_menu,
    optional_document_menu,
    yes_no_menu,
)
from app.bot.states import IdentityForm, KhodnevisForm
from app.db.models import Order, Service, ServiceCode, User
from app.db.session import SessionLocal
from app.utils.dates import gregorian_display, jalali_to_gregorian
from app.utils.ids import public_order_id

router = Router()
logger = logging.getLogger(__name__)


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
        return user


async def create_order(message: Message, service_code: ServiceCode) -> Order:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one()
        result = await session.execute(select(Service).where(Service.code == service_code.value))
        service = result.scalar_one()
        order = Order(
            public_id="PENDING",
            user_id=user.id,
            service_id=service.id,
            data_json=json.dumps({}, ensure_ascii=False),
        )
        session.add(order)
        await session.flush()
        order.public_id = public_order_id(order.id)
        await session.commit()
        await session.refresh(order)
        return order


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await get_or_create_user(message)
    await message.answer(
        "سلام 🌷\nبه «بات تثبیت هویت» خوش آمدید.\n\nخدمت موردنظر را انتخاب کنید:",
        reply_markup=main_menu(),
    )


@router.message(F.text == "🔄 شروع مجدد")
async def restart(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("فرآیند فعلی لغو شد. از منوی اصلی یک خدمت را انتخاب کنید.", reply_markup=main_menu())


@router.message(F.text == "🪪 تثبیت هویت")
async def identity_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    order = await create_order(message, ServiceCode.IDENTITY)
    await state.update_data(order_id=order.id, public_id=order.public_id, service_code=ServiceCode.IDENTITY.value)
    await state.set_state(IdentityForm.full_name)
    await message.answer("۱/۸\nنام و نام خانوادگی را وارد کنید:")


@router.message(IdentityForm.full_name)
async def identity_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    await state.set_state(IdentityForm.mobile)
    await message.answer("۲/۸\nشماره موبایل در دسترس را وارد کنید:")


@router.message(IdentityForm.mobile)
async def identity_mobile(message: Message, state: FSMContext) -> None:
    await state.update_data(mobile=message.text.strip())
    await state.set_state(IdentityForm.birth_date)
    await message.answer("۳/۸\nتاریخ تولد را به شمسی وارد کنید. مثال: ۱۴۰۵/۰۱/۱۵ یا 1405/01/15")


@router.message(IdentityForm.birth_date)
async def identity_birth(message: Message, state: FSMContext) -> None:
    try:
        value = jalali_to_gregorian(message.text)
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return
    await state.update_data(birth_date_gregorian=gregorian_display(value))
    await state.set_state(IdentityForm.return_date)
    await message.answer("۴/۸\nآخرین تاریخ بازگشت به افغانستان را به شمسی وارد کنید:")


@router.message(IdentityForm.return_date)
async def identity_return(message: Message, state: FSMContext) -> None:
    try:
        value = jalali_to_gregorian(message.text)
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
    await message.answer("۶/۸\nعکس مدرک شناسایی را ارسال کنید.")


@router.message(IdentityForm.identity_document, F.photo)
async def identity_document(message: Message, state: FSMContext) -> None:
    await state.update_data(identity_document=message.photo[-1].file_id)
    await state.set_state(IdentityForm.tazkira)
    await message.answer("۷/۸\nعکس تذکره را ارسال کنید.")


@router.message(IdentityForm.tazkira, F.photo)
async def identity_tazkira(message: Message, state: FSMContext) -> None:
    await state.update_data(tazkira=message.photo[-1].file_id)
    await state.set_state(IdentityForm.companion_choice)
    await message.answer("۸/۸\nآیا همراه دیگری دارید؟", reply_markup=yes_no_menu())


@router.message(IdentityForm.companion_choice)
async def identity_companion_choice(message: Message, state: FSMContext) -> None:
    if message.text == "✅ بله":
        await state.set_state(IdentityForm.companion_name)
        await message.answer("نام و نام خانوادگی همراه را وارد کنید:")
    elif message.text == "❌ خیر":
        await show_identity_summary(message, state)
    else:
        await message.answer("لطفاً «بله» یا «خیر» را انتخاب کنید.", reply_markup=yes_no_menu())


@router.message(IdentityForm.companion_name)
async def identity_companion_name(message: Message, state: FSMContext) -> None:
    await state.update_data(pending_companion_name=message.text.strip())
    await state.set_state(IdentityForm.companion_mobile)
    await message.answer("شماره همراه را وارد کنید:")


@router.message(IdentityForm.companion_mobile)
async def identity_companion_mobile(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    companions = data.get("companions", [])
    companions.append({"full_name": data["pending_companion_name"], "mobile": message.text.strip()})
    await state.update_data(companions=companions)
    await state.set_state(IdentityForm.companion_choice)
    await message.answer("آیا همراه دیگری دارید؟", reply_markup=yes_no_menu())


async def show_identity_summary(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    companions = data.get("companions", [])
    companion_text = "ندارد"
    if companions:
        companion_text = "\n".join(
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
        "برای ادامه «تأیید» را ارسال کنید یا «🔄 شروع مجدد» را بزنید."
    )


@router.message(IdentityForm.confirm, F.text == "تأیید")
async def identity_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await save_order_data(data)
    await state.set_state(IdentityForm.receipt)
    await message.answer(
        "💳 پرداخت به‌صورت کارت‌به‌کارت انجام می‌شود.\n"
        "پس از واریز، تصویر رسید را ارسال کنید.\n"
        "شماره کارت و مبلغ از پنل مدیریت قابل تنظیم است."
    )


@router.message(IdentityForm.receipt, F.photo)
async def identity_receipt(message: Message, state: FSMContext) -> None:
    await save_receipt(message, state)
    await state.clear()
    await message.answer("✅ رسید شما ثبت شد و برای بررسی ارسال گردید.", reply_markup=main_menu())


@router.message(F.text == "📝 کد رهگیری خودنویس")
async def khodnevis_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    order = await create_order(message, ServiceCode.KHODNEVIS)
    await state.update_data(order_id=order.id, public_id=order.public_id, service_code=ServiceCode.KHODNEVIS.value)
    await state.set_state(KhodnevisForm.full_name)
    await message.answer("۱/۷\nنام و نام خانوادگی را وارد کنید:")


@router.message(KhodnevisForm.full_name)
async def khodnevis_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    await state.set_state(KhodnevisForm.mobile)
    await message.answer("۲/۷\nشماره موبایل در دسترس را وارد کنید:")


@router.message(KhodnevisForm.mobile)
async def khodnevis_mobile(message: Message, state: FSMContext) -> None:
    await state.update_data(mobile=message.text.strip())
    await state.set_state(KhodnevisForm.document_type)
    await message.answer("۳/۷\nمدرک را انتخاب کنید:", reply_markup=document_type_menu())


@router.message(KhodnevisForm.document_type)
async def khodnevis_document_type(message: Message, state: FSMContext) -> None:
    if message.text == "🪪 کارت آمایش":
        await state.update_data(document_type="amayesh")
        await state.set_state(KhodnevisForm.amayesh)
        await message.answer("۴/۷\nعکس کارت آمایش را ارسال کنید.")
    elif message.text == "🛂 پاسپورت":
        await state.update_data(document_type="passport")
        await state.set_state(KhodnevisForm.passport_first)
        await message.answer("۴/۷\nعکس صفحه اول پاسپورت الزامی است.")
    else:
        await message.answer("یکی از دو گزینه را انتخاب کنید.", reply_markup=document_type_menu())


@router.message(KhodnevisForm.amayesh, F.photo)
async def khodnevis_amayesh(message: Message, state: FSMContext) -> None:
    await state.update_data(amayesh=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.own_mobile)
    await message.answer("شماره موبایل به نام خود شخص را وارد کنید:")


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
        await message.answer("حالا تصویر صفحه تمدید پاسپورت را ارسال کنید.")
        return
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
        await message.answer("شماره موبایل به نام خود شخص را وارد کنید:")
    elif message.text == "📸 ارسال تصویر":
        await message.answer("حالا تصویر صفحه تمدید اقامت/ویزا را ارسال کنید.")
    else:
        await message.answer("یکی از گزینه‌ها را انتخاب کنید.", reply_markup=optional_document_menu())


@router.message(KhodnevisForm.residence_renewal, F.photo)
async def khodnevis_residence_renewal_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(residence_renewal=message.photo[-1].file_id)
    await state.set_state(KhodnevisForm.own_mobile)
    await message.answer("شماره موبایل به نام خود شخص را وارد کنید:")


@router.message(KhodnevisForm.own_mobile)
async def khodnevis_own_mobile(message: Message, state: FSMContext) -> None:
    await state.update_data(own_mobile=message.text.strip())
    data = await state.get_data()
    await state.set_state(KhodnevisForm.confirm)
    await message.answer(
        "📋 خلاصه درخواست\n\n"
        f"نام: {data.get('full_name')}\n"
        f"موبایل در دسترس: {data.get('mobile')}\n"
        f"مدرک: {data.get('document_type')}\n"
        f"موبایل به نام شخص: {data.get('own_mobile')}\n\n"
        "برای ادامه «تأیید» را ارسال کنید."
    )


@router.message(KhodnevisForm.confirm, F.text == "تأیید")
async def khodnevis_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await save_order_data(data)
    await state.set_state(KhodnevisForm.receipt)
    await message.answer(
        "💳 پرداخت کارت‌به‌کارت است. پس از واریز، تصویر رسید را ارسال کنید."
    )


@router.message(KhodnevisForm.receipt, F.photo)
async def khodnevis_receipt(message: Message, state: FSMContext) -> None:
    await save_receipt(message, state)
    await state.clear()
    await message.answer("✅ رسید ثبت شد و در انتظار بررسی است.", reply_markup=main_menu())


async def save_order_data(data: dict) -> None:
    order_id = data["order_id"]
    excluded = {"order_id", "public_id", "service_code"}
    payload = {k: v for k, v in data.items() if k not in excluded}
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            return
        order.data_json = json.dumps(payload, ensure_ascii=False)
        order.status = "waiting_receipt_review"
        await session.commit()


async def save_receipt(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    async with SessionLocal() as session:
        order = await session.get(Order, data["order_id"])
        if order is None:
            return
        from app.db.models import Payment

        session.add(
            Payment(
                order_id=order.id,
                amount_toman=0,
                receipt_file_id=message.photo[-1].file_id,
                status="pending",
            )
        )
        order.status = "waiting_receipt_review"
        await session.commit()


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
        await message.answer("هنوز درخواستی ثبت نکرده‌اید.", reply_markup=main_menu())
        return
    text = "📋 درخواست‌های شما:\n\n"
    for order, service in rows:
        text += f"{order.public_id} — {service.name}\nوضعیت: {order.status}\n\n"
    await message.answer(text, reply_markup=main_menu())


@router.message(F.text == "👤 حساب من")
async def account(message: Message) -> None:
    user = await get_or_create_user(message)
    await message.answer(
        f"👤 حساب شما\nشناسه تلگرام: {user.telegram_id}\n"
        f"نام: {user.first_name or ''} {user.last_name or ''}".strip(),
        reply_markup=main_menu(),
    )


@router.message(F.text == "📞 پشتیبانی")
async def support(message: Message) -> None:
    await message.answer(
        "📞 پشتیبانی\nبرای ارتباط با پشتیبانی، پیام خود را همینجا ارسال کنید.",
        reply_markup=main_menu(),
    )
