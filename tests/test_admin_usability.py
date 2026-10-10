from app.bot.admin import admin_menu
from app.bot.keyboards import payment_choice_menu, support_menu


def test_admin_menu_exposes_core_management_sections():
    callbacks = {
        button.callback_data
        for row in admin_menu().inline_keyboard
        for button in row
    }
    assert {
        "adm:pending",
        "adm:orders",
        "adm:case",
        "adm:stats",
        "adm:users",
        "adm:operators",
        "adm:services",
        "adm:prices",
        "adm:card",
        "adm:wallets",
        "adm:topups",
        "adm:coupons",
        "adm:settings",
    } <= callbacks


def test_payment_choice_displays_live_credit_amount():
    keyboard = payment_choice_menu(125_000)
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    wallet_button = next(button for button in buttons if button.callback_data == "pay:wallet")
    assert "125,000 تومان" in wallet_button.text


def test_direct_support_link_uses_requested_account():
    keyboard = support_menu()
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    support_button = next(button for button in buttons if button.url)
    assert support_button.url == "https://t.me/NetYar_esf"
