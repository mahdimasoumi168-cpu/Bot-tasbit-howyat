from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🪪 تثبیت هویت")],
            [KeyboardButton(text="📝 کد رهگیری خودنویس")],
            [KeyboardButton(text="📋 پیگیری درخواست‌ها")],
            [KeyboardButton(text="👤 حساب من"), KeyboardButton(text="📞 پشتیبانی")],
            [KeyboardButton(text="🔄 شروع مجدد")],
        ],
        resize_keyboard=True,
    )


def consulate_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇦🇫 زاهدان"), KeyboardButton(text="🇦🇫 مشهد")],
            [KeyboardButton(text="🔄 شروع مجدد")],
        ],
        resize_keyboard=True,
    )


def yes_no_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ بله"), KeyboardButton(text="❌ خیر")],
            [KeyboardButton(text="🔄 شروع مجدد")],
        ],
        resize_keyboard=True,
    )


def document_type_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🪪 کارت آمایش"), KeyboardButton(text="🛂 پاسپورت")],
            [KeyboardButton(text="🔄 شروع مجدد")],
        ],
        resize_keyboard=True,
    )


def optional_document_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 ارسال تصویر"), KeyboardButton(text="⏭️ ندارم / رد کردن")],
            [KeyboardButton(text="🔄 شروع مجدد")],
        ],
        resize_keyboard=True,
    )
