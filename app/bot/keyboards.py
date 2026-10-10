from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False, is_operator: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🪪 تثبیت هویت", callback_data="menu:identity", style="primary"),
         InlineKeyboardButton(text="📝 کد رهگیری خودنویس", callback_data="menu:khodnevis", style="primary")],
        [InlineKeyboardButton(text="💰 اعتبار من", callback_data="menu:wallet", style="primary")],
        [InlineKeyboardButton(text="📋 پیگیری درخواست‌ها", callback_data="menu:tracking", style="primary"),
         InlineKeyboardButton(text="👤 حساب من", callback_data="menu:account", style="primary")],
        [InlineKeyboardButton(text="📞 پشتیبانی", callback_data="menu:support", style="primary"),
         InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart", style="primary")],
    ]
    if is_operator and is_admin:
        rows.append([
            InlineKeyboardButton(text="👨‍💼 پنل اپراتور", callback_data="menu:operator", style="primary"),
            InlineKeyboardButton(text="🛠 پنل مدیریت", callback_data="menu:admin", style="primary"),
        ])
    elif is_operator:
        rows.append([InlineKeyboardButton(text="👨‍💼 پنل اپراتور", callback_data="menu:operator", style="primary")])
    elif is_admin:
        rows.append([InlineKeyboardButton(text="🛠 پنل مدیریت", callback_data="menu:admin", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def consulate_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇦🇫 زاهدان", callback_data="identity:consulate:z", style="primary"),
         InlineKeyboardButton(text="🇦🇫 مشهد", callback_data="identity:consulate:m", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def yes_no_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ بله", callback_data="identity:companion:y", style="success"),
         InlineKeyboardButton(text="❌ خیر", callback_data="identity:companion:n", style="danger")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def document_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪪 کارت آمایش", callback_data="khodnevis:doc:amayesh", style="primary"),
         InlineKeyboardButton(text="🛂 پاسپورت", callback_data="khodnevis:doc:passport", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def identity_document_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪪 کارت آمایش", callback_data="identity:doc:amayesh", style="primary"),
         InlineKeyboardButton(text="🛂 پاسپورت", callback_data="identity:doc:passport", style="primary")],
        [InlineKeyboardButton(text="📄 سایر مدارک", callback_data="identity:doc:other", style="primary"),
         InlineKeyboardButton(text="⏭️ ندارم", callback_data="identity:doc:none", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def optional_document_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 ارسال تصویر", callback_data="khodnevis:optional:send", style="primary"),
         InlineKeyboardButton(text="⏭️ ندارم / رد کردن", callback_data="khodnevis:optional:skip", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def support_menu(active_orders: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="💬 ارتباط مستقیم با پشتیبانی", url="https://t.me/NetYar_esf", style="primary")],
    ]
    if active_orders:
        rows.append([InlineKeyboardButton(text="📋 پشتیبانی درخواست‌های من", callback_data="menu:support_orders", style="primary")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="flow:cancel", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_invoice_menu(card_number: str, amount_rial: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 کپی شماره کارت", copy_text=CopyTextButton(text=card_number), style="primary")],
        [InlineKeyboardButton(text="📋 کپی مبلغ ریالی", copy_text=CopyTextButton(text=str(amount_rial)), style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def admin_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="adm:cancel", style="danger")],
    ])


def single_action_menu(text: str = "🔄 شروع مجدد") -> InlineKeyboardMarkup:
    callback = "menu:restart" if text == "🔄 شروع مجدد" else "noop"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback, style="primary")]])


def confirm_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأیید و ادامه", callback_data="order:confirm", style="success")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def payment_choice_menu(credit: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💰 استفاده از اعتبار | {credit:,} تومان", callback_data="pay:wallet", style="success")],
        [InlineKeyboardButton(text="💳 کارت به کارت", callback_data="pay:card", style="primary")],
        [InlineKeyboardButton(text="🏷️ کد تخفیف", callback_data="pay:coupon", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])


def wallet_menu(balance: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزایش اعتبار", callback_data="wallet:topup", style="primary")],
        [InlineKeyboardButton(text="📜 تاریخچه اعتبار", callback_data="wallet:history", style="primary")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="flow:cancel", style="primary")],
    ])


def wallet_topup_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="flow:cancel", style="danger")],
    ])
