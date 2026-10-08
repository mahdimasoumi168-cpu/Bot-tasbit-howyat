from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False, is_operator: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🪪 تثبیت هویت", callback_data="menu:identity"), InlineKeyboardButton(text="📝 کد رهگیری خودنویس", callback_data="menu:khodnevis")],
        [InlineKeyboardButton(text="💰 اعتبار من", callback_data="menu:wallet")],
        [InlineKeyboardButton(text="📋 پیگیری درخواست‌ها", callback_data="menu:tracking"), InlineKeyboardButton(text="👤 حساب من", callback_data="menu:account")],
        [InlineKeyboardButton(text="📞 پشتیبانی", callback_data="menu:support"), InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")],
    ]
    if is_operator and is_admin:
        rows.append([InlineKeyboardButton(text="👨‍💼 پنل اپراتور", callback_data="menu:operator"), InlineKeyboardButton(text="🛠 پنل مدیریت", callback_data="menu:admin")])
    elif is_operator:
        rows.append([InlineKeyboardButton(text="👨‍💼 پنل اپراتور", callback_data="menu:operator")])
    elif is_admin:
        rows.append([InlineKeyboardButton(text="🛠 پنل مدیریت", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def consulate_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇦🇫 زاهدان", callback_data="identity:consulate:z"), InlineKeyboardButton(text="🇦🇫 مشهد", callback_data="identity:consulate:m")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])


def yes_no_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ بله", callback_data="identity:companion:y"), InlineKeyboardButton(text="❌ خیر", callback_data="identity:companion:n")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])


def document_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪪 کارت آمایش", callback_data="khodnevis:doc:amayesh"), InlineKeyboardButton(text="🛂 پاسپورت", callback_data="khodnevis:doc:passport")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])


def identity_document_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪪 کارت آمایش", callback_data="identity:doc:amayesh"), InlineKeyboardButton(text="🛂 پاسپورت", callback_data="identity:doc:passport")],
        [InlineKeyboardButton(text="📄 سایر مدارک", callback_data="identity:doc:other"), InlineKeyboardButton(text="⏭️ ندارم", callback_data="identity:doc:none")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])


def optional_document_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 ارسال تصویر", callback_data="khodnevis:optional:send"), InlineKeyboardButton(text="⏭️ ندارم / رد کردن", callback_data="khodnevis:optional:skip")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])



def support_menu(active_orders: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="💬 ارتباط مستقیم با پشتیبانی", url="https://t.me/Good_ok_2000")],
    ]
    if active_orders:
        rows.append([InlineKeyboardButton(text="📋 پشتیبانی درخواست‌های من", callback_data="menu:support_orders")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="flow:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_invoice_menu(card_number: str, amount_rial: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 کپی شماره کارت", copy_text=CopyTextButton(text=card_number))],
        [InlineKeyboardButton(text="📋 کپی مبلغ ریالی", copy_text=CopyTextButton(text=str(amount_rial)))],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])




def cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])


def admin_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="adm:cancel")],
    ])


def single_action_menu(text: str = "🔄 شروع مجدد") -> InlineKeyboardMarkup:
    callback = "menu:restart" if text == "🔄 شروع مجدد" else "noop"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)]])


def confirm_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأیید و ادامه", callback_data="order:confirm")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])



def payment_choice_menu(credit: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 استفاده از اعتبار | {credit:,} تومان", callback_data="pay:wallet")],
        [InlineKeyboardButton(text="💳 کارت به کارت", callback_data="pay:card")],
        [InlineKeyboardButton(text="🏷️ کد تخفیف", callback_data="pay:coupon")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])


def wallet_menu(balance: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزایش اعتبار", callback_data="wallet:topup")],
        [InlineKeyboardButton(text="📜 تاریخچه اعتبار", callback_data="wallet:history")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="flow:cancel")],
    ])


def wallet_topup_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel")],
    ])
