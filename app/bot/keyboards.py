from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🪪 تثبیت هویت")],
        [KeyboardButton(text="📝 کد رهگیری خودنویس")],
        [KeyboardButton(text="📋 پیگیری درخواست‌ها")],
        [KeyboardButton(text="👤 حساب من"), KeyboardButton(text="📞 پشتیبانی")],
        [KeyboardButton(text="🔄 شروع مجدد")],
    ]
    if is_admin:
        rows.insert(-1, [KeyboardButton(text="🛠 پنل مدیریت")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def consulate_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🇦🇫 زاهدان"), KeyboardButton(text="🇦🇫 مشهد")]],
        resize_keyboard=True,
    )


def yes_no_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ بله"), KeyboardButton(text="❌ خیر")]],
        resize_keyboard=True,
    )


def document_type_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🪪 کارت آمایش"), KeyboardButton(text="🛂 پاسپورت")]],
        resize_keyboard=True,
    )


def optional_document_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📸 ارسال تصویر"), KeyboardButton(text="⏭️ ندارم / رد کردن")]],
        resize_keyboard=True,
    )


def single_action_menu(text: str = "🔄 شروع مجدد") -> ReplyKeyboardMarkup:
    """فقط یک دکمه لازم در مراحل ورود اطلاعات را نمایش می‌دهد."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
    )
