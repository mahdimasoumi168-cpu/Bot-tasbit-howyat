from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

VPN_PRICE_PER_GB_TOMAN = 10_000
VPN_MIN_GB = 10
VPN_MAX_GB = 100
VPN_STEP_GB = 10


def vpn_price_toman(gigabytes: int) -> int:
    if gigabytes < VPN_MIN_GB or gigabytes > VPN_MAX_GB or gigabytes % VPN_STEP_GB:
        raise ValueError("حجم انتخابی باید از ۱۰ تا ۱۰۰ گیگ و با فاصله‌های ۱۰ گیگ باشد.")
    return gigabytes * VPN_PRICE_PER_GB_TOMAN


def vpn_duration_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=f"{months} ماه", callback_data=f"vpn:months:{months}", style="primary")
            for months in (1, 2)
        ],
        [
            InlineKeyboardButton(text=f"{months} ماه", callback_data=f"vpn:months:{months}", style="primary")
            for months in (3, 4)
        ],
        [InlineKeyboardButton(text="🔙 بازگشت به صفحه اصلی", callback_data="menu:home", style="primary")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vpn_data_menu(months: int) -> InlineKeyboardMarkup:
    rows = []
    for first in range(VPN_MIN_GB, VPN_MAX_GB + 1, 20):
        rows.append([
            InlineKeyboardButton(
                text=f"{gigabytes} گیگابایت",
                callback_data=f"vpn:gb:{months}:{gigabytes}",
                style="primary",
            )
            for gigabytes in (first, first + VPN_STEP_GB)
            if gigabytes <= VPN_MAX_GB
        ])
    rows.extend([
        [InlineKeyboardButton(text="🔙 انتخاب مدت", callback_data="vpn:start", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="menu:home", style="danger")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vpn_summary_menu(months: int, gigabytes: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 ادامه به پرداخت", callback_data=f"vpn:pay:{months}:{gigabytes}", style="primary")],
        [InlineKeyboardButton(text="🔙 تغییر حجم", callback_data=f"vpn:months:{months}", style="primary")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="menu:home", style="danger")],
    ])


@router.callback_query(F.data == "vpn:start")
async def vpn_start(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "🔐 خرید VPN / فیلترشکن\n\nمدت اشتراک را انتخاب کنید:",
        reply_markup=vpn_duration_menu(),
    )


@router.callback_query(F.data.startswith("vpn:months:"))
async def vpn_choose_months(callback: CallbackQuery) -> None:
    try:
        months = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer("مدت انتخابی معتبر نیست.", show_alert=True)
        return
    if months not in (1, 2, 3, 4):
        await callback.answer("مدت باید بین ۱ تا ۴ ماه باشد.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        f"🔐 مدت انتخابی: {months} ماه\n\nحجم موردنیاز را انتخاب کنید (۱۰ تا ۱۰۰ گیگابایت، هر بار ۱۰ گیگ):",
        reply_markup=vpn_data_menu(months),
    )


@router.callback_query(F.data.startswith("vpn:gb:"))
async def vpn_choose_data(callback: CallbackQuery) -> None:
    try:
        _, _, raw_months, raw_gigabytes = callback.data.split(":")
        months = int(raw_months)
        gigabytes = int(raw_gigabytes)
        amount = vpn_price_toman(gigabytes)
    except (ValueError, AttributeError):
        await callback.answer("مدت یا حجم انتخابی معتبر نیست.", show_alert=True)
        return
    if months not in (1, 2, 3, 4):
        await callback.answer("مدت باید بین ۱ تا ۴ ماه باشد.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "🧾 خلاصه سفارش VPN\n\n"
        f"⏳ مدت اشتراک: {months} ماه\n"
        f"📦 حجم: {gigabytes} گیگابایت\n"
        f"💰 قیمت هر گیگابایت: {VPN_PRICE_PER_GB_TOMAN:,} تومان\n"
        f"💵 مبلغ کل: {amount:,} تومان\n\n"
        "درگاه پرداخت در حال حاضر متصل نیست؛ برای جلوگیری از پرداخت ناموفق، قبل از فعال‌شدن درگاه هیچ مبلغی واریز نکنید.",
        reply_markup=vpn_summary_menu(months, gigabytes),
    )


@router.callback_query(F.data.startswith("vpn:pay:"))
async def vpn_payment_unavailable(callback: CallbackQuery) -> None:
    try:
        _, _, raw_months, raw_gigabytes = callback.data.split(":")
        months = int(raw_months)
        gigabytes = int(raw_gigabytes)
        vpn_price_toman(gigabytes)
    except (ValueError, AttributeError):
        await callback.answer("اطلاعات سفارش معتبر نیست.", show_alert=True)
        return
    if months not in (1, 2, 3, 4):
        await callback.answer("مدت اشتراک معتبر نیست.", show_alert=True)
        return
    await callback.answer("درگاه متصل نمی‌باشد.", show_alert=True)
    await callback.message.answer(
        "⚠️ درگاه پرداخت VPN متصل نمی‌باشد.\n\n"
        "فعلاً امکان پرداخت یا ثبت نهایی سفارش وجود ندارد. لطفاً هیچ مبلغی واریز نکنید؛ "
        "پس از اتصال درگاه، امکان خرید اعلام خواهد شد."
    )
