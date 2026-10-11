from app.bot.handlers import normalize_mobile, valid_mobile, valid_name, valid_identity_document_number


def test_mobile_validation_and_normalization():
    assert valid_mobile("09123456789")
    assert valid_mobile("۰۹۱۲۳۴۵۶۷۸۹")
    assert valid_mobile("+989123456789")
    assert normalize_mobile("۰۹۱۲۳۴۵۶۷۸۹") == "09123456789"
    assert not valid_mobile("0912345678")
    assert not valid_mobile("1234567890")


def test_name_validation():
    assert valid_name("احمد محمدی")
    assert valid_name("Ali Ahmadi")
    assert not valid_name("احمد")
    assert not valid_name("۱۲۳۴۵")
    assert not valid_name("A")
    assert not valid_name("A" * 81)



def test_inline_buttons_have_semantic_styles():
    from app.bot.keyboards import main_menu, payment_choice_menu

    main = main_menu()
    assert all(button.style is not None for row in main.inline_keyboard for button in row)

    payment = payment_choice_menu(500000)
    styles = [button.style for row in payment.inline_keyboard for button in row]
    assert "success" in styles
    assert "danger" in styles
    assert "primary" in styles


def test_receipt_retry_is_only_available_after_payment_receipt_rejection():
    from app.bot.handlers import can_retry_receipt

    assert can_retry_receipt("rejected", "rejected")
    assert not can_retry_receipt("rejected", "approved")
    assert not can_retry_receipt("completed", "rejected")
    assert not can_retry_receipt("deleted", "rejected")
    assert not can_retry_receipt("rejected", None)


def test_card_payment_requires_complete_destination_details():
    from app.bot.handlers import card_details_ready

    assert card_details_ready("1234567890123456", "سید فرید معصومی")
    assert not card_details_ready("", "سید فرید معصومی")
    assert not card_details_ready("1234567890123456", "")
    assert not card_details_ready(None, None)



def test_identity_document_number_validation():
    assert valid_identity_document_number("A1234567")
    assert valid_identity_document_number("۱۲۳۴۵۶۷۸")
    assert valid_identity_document_number("AB-123 / 45")
    assert not valid_identity_document_number(None)
    assert not valid_identity_document_number("")
    assert not valid_identity_document_number("1")
    assert not valid_identity_document_number("X" * 65)


def test_identity_form_asks_for_document_number_after_photo_and_shows_it_in_admin_case():
    from pathlib import Path

    handler_source = Path("app/bot/handlers.py").read_text(encoding="utf-8")
    state_source = Path("app/bot/states.py").read_text(encoding="utf-8")
    admin_source = Path("app/bot/admin.py").read_text(encoding="utf-8")

    photo_step = handler_source.split(
        '@router.message(IdentityForm.identity_document, F.photo)', 1
    )[1].split('@router.message(IdentityForm.identity_document_number, F.text)', 1)[0]
    number_step = handler_source.split(
        '@router.message(IdentityForm.identity_document_number, F.text)', 1
    )[1].split('@router.message(IdentityForm.identity_document_number)', 1)[0]

    assert "IdentityForm.identity_document_number" in photo_step
    assert "identity_document_number=value" in number_step
    assert "IdentityForm.tazkira" in number_step
    assert "identity_document_number = State()" in state_source
    assert '"identity_document_number": "شماره شناسه مدرک شناسایی"' in admin_source
