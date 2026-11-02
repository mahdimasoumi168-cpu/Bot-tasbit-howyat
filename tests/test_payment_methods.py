from app.bot.keyboards import payment_choice_menu, wallet_topup_choice_menu


def test_service_payment_menu_offers_card_and_rialit():
    menu = payment_choice_menu(0, rialit_available=True)
    callbacks = {
        button.callback_data
        for row in menu.inline_keyboard
        for button in row
        if button.callback_data
    }
    assert {"pay:card", "pay:rialit"} <= callbacks
    assert not any("jibit" in callback.lower() for callback in callbacks)


def test_wallet_topup_menu_offers_only_rialit_and_card():
    menu = wallet_topup_choice_menu()
    callbacks = {
        button.callback_data
        for row in menu.inline_keyboard
        for button in row
        if button.callback_data
    }
    assert callbacks == {
        "wallet:topup:rialit",
        "wallet:topup:card",
        "flow:cancel",
    }



def test_wallet_topup_hides_rialit_when_amount_is_out_of_range():
    menu = wallet_topup_choice_menu(rialit_available=False)
    callbacks = {
        button.callback_data
        for row in menu.inline_keyboard
        for button in row
        if button.callback_data
    }
    assert callbacks == {"wallet:topup:card", "flow:cancel"}
