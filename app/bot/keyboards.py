from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False, is_operator: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🪪 تثبیت هویت", callback_data="menu:identity"), InlineKeyboardButton(text="📝 کد رهگیری خودنویس", callback_data="menu:khodnevis")],
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
        [InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")],
    ])


def yes_no_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ بله", callback_data="identity:companion:y"), InlineKeyboardButton(text="❌ خیر", callback_data="identity:companion:n")],
        [InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")],
    ])


def document_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪪 کارت آمایش", callback_data="khodnevis:doc:amayesh"), InlineKeyboardButton(text="🛂 پاسپورت", callback_data="khodnevis:doc:passport")],
        [InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")],
    ])


def optional_document_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 ارسال تصویر", callback_data="khodnevis:optional:send"), InlineKeyboardButton(text="⏭️ ندارم / رد کردن", callback_data="khodnevis:optional:skip")],
        [InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")],
    ])


def single_action_menu(text: str = "🔄 شروع مجدد") -> InlineKeyboardMarkup:
    callback = "menu:restart" if text == "🔄 شروع مجدد" else "noop"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)]])


def confirm_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأیید و ادامه", callback_data="order:confirm")],
        [InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="menu:restart")],
    ])
