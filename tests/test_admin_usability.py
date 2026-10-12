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


def test_payment_options_include_variza_gateway():
    from app.bot.keyboards import wallet_topup_choice_menu

    payment_buttons = [
        button
        for row in payment_choice_menu(50_000).inline_keyboard
        for button in row
    ]
    topup_buttons = [
        button
        for row in wallet_topup_choice_menu().inline_keyboard
        for button in row
    ]

    assert {button.callback_data for button in payment_buttons} >= {
        "pay:wallet", "pay:card", "pay:coupon", "pay:variza"
    }
    assert {button.callback_data for button in topup_buttons} == {
        "wallet:topup:variza", "wallet:topup:card", "flow:cancel"
    }


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


def test_setserviceprice_command_is_handled_by_unrestricted_admin_router():
    from pathlib import Path

    handlers_source = Path("app/bot/handlers.py").read_text(encoding="utf-8")
    admin_source = Path("app/bot/admin.py").read_text(encoding="utf-8")

    # handlers router is registered before admin router; a limited handler here
    # would intercept the command and reject identity/khodnevis service codes.
    assert '@router.message(F.text.startswith("/setserviceprice"))' not in handlers_source
    assert '@router.message(F.text.regexp(r"^/(?:setprice|setserviceprice)(?:\\s|$)"))' in admin_source


def test_services_menu_can_hide_disabled_services():
    keyboard = services_menu({"identity", "fida"})
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    callbacks = {button.callback_data for button in buttons}
    assert {"menu:identity", "menu:fida", "menu:home"} <= callbacks
    assert not {"menu:khodnevis", "menu:dolatman", "menu:screening", "menu:other_service"} & callbacks



def test_admin_price_command_rejects_zero_tariff():
    from pathlib import Path

    source = Path("app/bot/admin.py").read_text(encoding="utf-8")
    command_block = source.split(
        '@router.message(F.text.regexp(r"^/(?:setprice|setserviceprice)(?:\\s|$)"))',
        1,
    )[1].split('@router.callback_query(F.data == "adm:stats")', 1)[0]
    assert "if price <= 0:" in command_block



def test_unapproved_receipts_stay_out_of_request_and_case_views():
    from pathlib import Path

    admin_source = Path("app/bot/admin.py").read_text(encoding="utf-8")
    handlers_source = Path("app/bot/handlers.py").read_text(encoding="utf-8")

    request_list = admin_source.split(
        '@router.callback_query(F.data == "adm:orders")', 1
    )[1].split("async def send_case_to_operator", 1)[0]
    operator_list = admin_source.split(
        "async def _show_operator_orders", 1
    )[1].split('@router.callback_query(F.data == "op:orders")', 1)[0]
    admin_detail = admin_source.split(
        '@router.callback_query(F.data.startswith("adm:order:"))', 1
    )[1].split('@router.callback_query(F.data.startswith("adm:delete:confirm:"))', 1)[0]
    case_lookup = admin_source.split(
        "async def case_lookup(message: Message", 1
    )[1].split("async def send_payment_receipt", 1)[0]
    case_dispatch = admin_source.split(
        "async def send_case_to_operator", 1
    )[1].split('@router.callback_query(F.data.startswith("adm:approve:"))', 1)[0]
    user_tracking = handlers_source.split(
        "async def track_orders", 1
    )[1].split('@router.callback_query(F.data.startswith("user:order:"))', 1)[0]

    for block in (request_list, operator_list, admin_detail, case_lookup, case_dispatch, user_tracking):
        assert 'Payment.status == "approved"' in block



def test_wallet_topup_requires_payment_choice_before_receipt_upload():
    from pathlib import Path

    source = Path("app/bot/handlers.py").read_text(encoding="utf-8")
    amount_block = source.split(
        "async def wallet_topup_amount", 1
    )[1].split('@router.callback_query(F.data == "wallet:topup:card")', 1)[0]
    card_block = source.split(
        '@router.callback_query(F.data == "wallet:topup:card")', 1
    )[1].split("async def wallet_topup_invoice", 1)[0]
    assert "await state.set_state(WalletTopupForm.choice)" in amount_block
    assert "await state.get_state() != WalletTopupForm.choice" in card_block
