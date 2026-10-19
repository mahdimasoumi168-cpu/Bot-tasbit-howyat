import pytest

from app.bot.keyboards import main_menu
from app.bot.vpn import (
    VPN_PRICE_PER_GB_TOMAN,
    vpn_data_menu,
    vpn_duration_menu,
    vpn_price_toman,
    vpn_summary_menu,
)


def test_vpn_price_is_ten_thousand_toman_per_gigabyte():
    assert vpn_price_toman(10) == 100_000
    assert vpn_price_toman(50) == 500_000
    assert vpn_price_toman(100) == 1_000_000
    assert VPN_PRICE_PER_GB_TOMAN == 10_000


@pytest.mark.parametrize("gigabytes", [0, 9, 11, 101, 110, -10])
def test_vpn_rejects_invalid_data_sizes(gigabytes):
    with pytest.raises(ValueError):
        vpn_price_toman(gigabytes)


def test_vpn_duration_menu_has_one_to_four_months():
    buttons = [
        button
        for row in vpn_duration_menu().inline_keyboard
        for button in row
    ]
    assert {button.callback_data for button in buttons if button.callback_data.startswith("vpn:months:")} == {
        "vpn:months:1",
        "vpn:months:2",
        "vpn:months:3",
        "vpn:months:4",
    }


def test_vpn_data_menu_has_ten_to_one_hundred_gigabytes_by_tens():
    buttons = [
        button
        for row in vpn_data_menu(2).inline_keyboard
        for button in row
    ]
    callbacks = {
        button.callback_data
        for button in buttons
        if button.callback_data and button.callback_data.startswith("vpn:gb:")
    }
    assert callbacks == {f"vpn:gb:2:{gigabytes}" for gigabytes in range(10, 101, 10)}


def test_vpn_summary_offers_payment_but_does_not_create_a_payment_link():
    buttons = [
        button
        for row in vpn_summary_menu(1, 10).inline_keyboard
        for button in row
    ]
    assert any(button.callback_data == "vpn:pay:1:10" for button in buttons)
    assert not any(button.url for button in buttons)


def test_home_menu_includes_vpn_button():
    buttons = [
        button
        for row in main_menu().inline_keyboard
        for button in row
    ]
    assert any(button.text == "🔐 VPN فیلترشکن" and button.callback_data == "vpn:start" for button in buttons)
