from app.bot.admin import admin_menu, document_review_keyboard
from app.bot.keyboards import payment_choice_menu, support_menu
from app.db.models import Document, Operator


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


def test_pending_document_has_review_actions_and_reviewed_document_does_not():
    pending = document_review_keyboard(Document(id=77, review_status="pending"))
    assert pending is not None
    callbacks = {
        button.callback_data
        for row in pending.inline_keyboard
        for button in row
    }
    assert callbacks == {"adm:doc:approve:77", "adm:doc:reject:77"}
    assert document_review_keyboard(Document(id=78, review_status="approved")) is None


def test_document_review_actions_require_operator_permission():
    document = Document(id=79, review_status="pending")
    without_permission = Operator(
        telegram_id=123,
        permissions_json='{"view_orders": true}',
        active=True,
    )
    with_permission = Operator(
        telegram_id=124,
        permissions_json='{"review_documents": true}',
        active=True,
    )
    assert document_review_keyboard(document, operator=without_permission) is None
    assert document_review_keyboard(document, operator=with_permission) is not None
