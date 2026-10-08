from app.bot.handlers import normalize_mobile, valid_mobile, valid_name


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
