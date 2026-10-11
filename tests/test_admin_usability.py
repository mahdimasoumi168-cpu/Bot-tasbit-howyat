from app.bot.admin import admin_menu, document_review_keyboard
from app.bot.keyboards import main_menu, payment_choice_menu, service_rules_menu, services_menu, support_menu
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
        "adm:rules",
        "adm:deleted",
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



def test_main_menu_groups_services_under_one_button():
    keyboard = main_menu()
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    labels = {button.text for button in buttons}
    callbacks = {button.callback_data for button in buttons}
    assert "🧾 خدمات دفتر نت یار مهاجر" in labels
    assert "🪪 تثبیت هویت" not in labels
    assert "📝 کد رهگیری خودنویس" not in labels
    assert "menu:services" in callbacks
    assert {"menu:wallet", "menu:account", "menu:tracking", "menu:restart", "menu:support"} <= callbacks


def test_services_menu_contains_both_services_and_home_return():
    keyboard = services_menu()
    callbacks = {button.callback_data for row in keyboard.inline_keyboard for button in row}
    assert {"menu:identity", "menu:khodnevis", "menu:home"} <= callbacks


def test_service_rules_menu_has_accept_and_reject_actions():
    keyboard = service_rules_menu("identity")
    callbacks = {button.callback_data for row in keyboard.inline_keyboard for button in row}
    assert callbacks == {"service:accept:identity", "service:reject:identity"}


def test_admin_menu_exposes_direct_message_action():
    callbacks = {
        button.callback_data
        for row in admin_menu().inline_keyboard
        for button in row
    }
    assert "adm:send_user" in callbacks


def test_admin_pending_receipts_includes_service_and_wallet_topups():
    from pathlib import Path

    source = Path("app/bot/admin.py").read_text(encoding="utf-8")
    pending_block = source.split('@router.callback_query(F.data == "adm:pending")', 1)[1].split(
        '@router.callback_query(F.data == "adm:orders")', 1
    )[0]
    assert "select(Payment, Order, Service, User)" in pending_block
    assert "select(WalletTopup, User)" in pending_block
    assert "adm:topup:view:" in pending_block


def test_form_prompts_hide_internal_limits_but_validation_remains():
    from app.bot.handlers import valid_mobile, valid_name
    from pathlib import Path

    source = Path("app/bot/handlers.py").read_text(encoding="utf-8")
    assert "محدودیت:" not in source
    assert valid_mobile("09123456789")
    assert not valid_mobile("123")
    assert valid_name("احمد محمدی")
    assert not valid_name("احمد")
