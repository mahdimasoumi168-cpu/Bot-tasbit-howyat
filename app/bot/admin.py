from aiogram import F,Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup,Message
from sqlalchemy import select
from app.bot.states import AdminForm
from app.core.config import get_settings
from app.db.models import Companion,Document,Order,Payment,Service,Ticket,TicketMessage,User
from app.db.session import SessionLocal
from app.bot.handlers import STATUS_TEXT

router=Router()

def is_admin(message:Message)->bool:
    return message.from_user.id in get_settings().admin_id_set

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔵 رسیدهای در انتظار بررسی",callback_data="adm:pending")],
        [InlineKeyboardButton(text="📋 آخرین درخواست‌ها",callback_data="adm:orders")]
    ])

def order_actions(order_id:int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأیید پرداخت",callback_data=f"adm:approve:{order_id}")],
        [InlineKeyboardButton(text="❌ رد پرداخت",callback_data=f"adm:reject:{order_id}")],
        [InlineKeyboardButton(text="💬 پیام به مشترک",callback_data=f"adm:msg:{order_id}")]
    ])

def status_header(order:Order,service:Service)->str:
    return f"{order.public_id} | {STATUS_TEXT.get(order.status,order.status)}\n🪪 خدمت: {service.name}"

@router.message(F.text=="/admin")
async def admin_start(message:Message):
    if not is_admin(message):return
    await message.answer("🛠 پنل مدیریت",reply_markup=admin_menu())

@router.callback_query(F.data=="adm:pending")
async def pending(callback:CallbackQuery):
    if callback.from_user.id not in get_settings().admin_id_set:return
    async with SessionLocal() as session:
        result=await session.execute(select(Payment,Order,Service,User).join(Order,Payment.order_id==Order.id)
            .join(Service,Order.service_id==Service.id).join(User,Order.user_id==User.id)
            .where(Payment.status=="pending").order_by(Payment.id.desc()).limit(20))
        rows=result.all()
    if not rows:await callback.message.edit_text("رسید در انتظار بررسی وجود ندارد.",reply_markup=admin_menu());return
    text="🔵 رسیدهای در انتظار بررسی:\n\n"
    for p,o,s,u in rows:text+=f"{o.public_id} — {s.name} — {u.first_name or ''} {u.last_name or ''}\n💰 {p.amount_toman:,} تومان\n\n"
    await callback.message.edit_text(text)
    for p,o,s,u in rows:
        await callback.message.answer(f"{status_header(o,s)}\n👤 {u.first_name or ''} {u.last_name or ''}\n📱 شناسه تلگرام: {u.telegram_id}\n💰 مبلغ: {p.amount_toman:,} تومان",reply_markup=order_actions(o.id))
        if p.receipt_file_id:await callback.message.answer_photo(p.receipt_file_id,caption=f"🧾 رسید {o.public_id}")

@router.callback_query(F.data=="adm:orders")
async def orders(callback:CallbackQuery):
    if callback.from_user.id not in get_settings().admin_id_set:return
    async with SessionLocal() as session:
        result=await session.execute(select(Order,Service,User).join(Service,Order.service_id==Service.id)
            .join(User,Order.user_id==User.id).order_by(Order.id.desc()).limit(20))
        rows=result.all()
    text="📋 آخرین درخواست‌ها:\n\n"
    for o,s,u in rows:text+=f"{o.public_id} | {STATUS_TEXT.get(o.status,o.status)} | {s.name} | {u.telegram_id}\n"
    await callback.message.edit_text(text or "درخواستی ثبت نشده است.",reply_markup=admin_menu())

async def send_case_to_operator(bot,order_id:int):
    settings=get_settings()
    async with SessionLocal() as session:
        result=await session.execute(select(Order,Service,User).join(Service,Order.service_id==Service.id).join(User,Order.user_id==User.id).where(Order.id==order_id))
        row=result.one_or_none()
        if not row:return
        order,service,user=row
        docs=(await session.execute(select(Document).where(Document.order_id==order.id).order_by(Document.id))).scalars().all()
        companions=(await session.execute(select(Companion).where(Companion.order_id==order.id))).scalars().all()
        payload=order.data_json
    import json
    data=json.loads(payload or "{}")
    text=(f"{status_header(order,service)}\n👤 مشترک: {data.get('full_name','')}\n"
          f"📱 موبایل در دسترس: {data.get('mobile','')}\n")
    if service.code=="identity":
        text+=f"🎂 تاریخ تولد: {data.get('birth_date_gregorian','')}\n✈️ آخرین تاریخ بازگشت به افغانستان: {data.get('return_date_gregorian','')}\n"
        text+=f"🇦🇫 کنسولگری: {data.get('consulate','')}\n"
        text+="👥 همراهان: "+("ندارد" if not companions else "دارد") 
        if companions:
            text+="\n"+"\n".join(f"• {x.full_name} — {x.mobile}" for x in companions)
    else:
        text+=f"🪪 مدرک: {data.get('document_type','')}\n📱 موبایل به نام شخص: {data.get('own_mobile','')}\n"
    for admin_id in settings.admin_id_set:
        await bot.send_message(admin_id,text,reply_markup=order_actions(order.id))
        for d in docs:
            await bot.send_photo(admin_id,d.telegram_file_id,caption=f"📎 {d.document_type} | {order.public_id}")

@router.callback_query(F.data.startswith("adm:approve:"))
async def approve(callback:CallbackQuery):
    if callback.from_user.id not in get_settings().admin_id_set:return
    order_id=int(callback.data.rsplit(":",1)[1])
    async with SessionLocal() as session:
        order=await session.get(Order,order_id)
        payment=(await session.execute(select(Payment).where(Payment.order_id==order_id).order_by(Payment.id.desc()))).scalars().first()
        if not order or not payment:await callback.answer("درخواست یا رسید پیدا نشد.",show_alert=True);return
        payment.status="approved";order.status="payment_approved"
        ticket=await session.execute(select(Ticket).where(Ticket.order_id==order_id))
        if ticket.scalar_one_or_none() is None:session.add(Ticket(order_id=order_id,status="open"))
        await session.commit()
        user=await session.get(User,order.user_id)
    await callback.answer("پرداخت تأیید شد.")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.bot.send_message(user.telegram_id,f"✅ پرداخت درخواست #{10000+order_id} تأیید شد.\nدرخواست شما وارد مرحله انجام شد.")
    await send_case_to_operator(callback.bot,order_id)

@router.callback_query(F.data.startswith("adm:reject:"))
async def reject(callback:CallbackQuery):
    if callback.from_user.id not in get_settings().admin_id_set:return
    order_id=int(callback.data.rsplit(":",1)[1])
    async with SessionLocal() as session:
        order=await session.get(Order,order_id)
        payment=(await session.execute(select(Payment).where(Payment.order_id==order_id).order_by(Payment.id.desc()))).scalars().first()
        if not order or not payment:return
        payment.status="rejected";order.status="rejected";user=await session.get(User,order.user_id);await session.commit()
    await callback.answer("رسید رد شد.")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.bot.send_message(user.telegram_id,f"❌ رسید درخواست #{10000+order_id} تأیید نشد.\nلطفاً رسید صحیح را دوباره ارسال کنید.")

@router.callback_query(F.data.startswith("adm:msg:"))
async def start_message(callback:CallbackQuery,state:FSMContext):
    if callback.from_user.id not in get_settings().admin_id_set:return
    order_id=int(callback.data.rsplit(":",1)[1]);await state.update_data(admin_order_id=order_id);await state.set_state(AdminForm.send_message)
    await callback.answer();await callback.message.answer("💬 پیام خود را ارسال کنید. متن، عکس، فایل، ویدیو یا صوت قابل ارسال است.")

@router.message(AdminForm.send_message)
async def send_message_to_user(message:Message,state:FSMContext):
    if not is_admin(message):return
    data=await state.get_data();order_id=data["admin_order_id"]
    async with SessionLocal() as session:
        row=(await session.execute(select(Order,Service,User).join(Service,Order.service_id==Service.id).join(User,Order.user_id==User.id).where(Order.id==order_id))).one_or_none()
        ticket=(await session.execute(select(Ticket).where(Ticket.order_id==order_id))).scalar_one_or_none()
        if not row or not ticket:await state.clear();await message.answer("تیکت فعال پیدا نشد.");return
        order,service,user=row
        session.add(TicketMessage(ticket_id=ticket.id,sender_type="admin",sender_telegram_id=message.from_user.id,
            content_type=message.content_type,text=message.text or message.caption))
        await session.commit()
    header=status_header(order,service)
    await message.bot.send_message(user.telegram_id,header)
    await message.copy_to(user.telegram_id)
    await state.clear()
    await message.answer("✅ پیام ارسال شد.")

@router.message()
async def user_ticket_reply(message:Message):
    if message.from_user.id in get_settings().admin_id_set:return
    async with SessionLocal() as session:
        result=await session.execute(select(Ticket,Order,Service).join(Order,Ticket.order_id==Order.id).join(Service,Order.service_id==Service.id)
            .join(User,Order.user_id==User.id).where(User.telegram_id==message.from_user.id,Ticket.status=="open").order_by(Ticket.id.desc()))
        row=result.first()
        if not row:return
        ticket,order,service=row
        session.add(TicketMessage(ticket_id=ticket.id,sender_type="user",sender_telegram_id=message.from_user.id,
            content_type=message.content_type,text=message.text or message.caption))
        await session.commit()
    for admin_id in get_settings().admin_id_set:
        await message.bot.send_message(admin_id,status_header(order,service)+f"\n👤 پاسخ مشترک: {message.from_user.id}")
        await message.copy_to(admin_id)
