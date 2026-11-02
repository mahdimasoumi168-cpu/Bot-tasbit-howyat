from app.payments.rialit import expected_rialit_payer_amount, rialit_amount_breakdown


def test_rialit_fee_is_exactly_twelve_percent_of_base_amount() -> None:
    assert expected_rialit_payer_amount(100_000) == 112_000
    assert expected_rialit_payer_amount(5_600) == 6_272


def test_rialit_amount_breakdown() -> None:
    assert rialit_amount_breakdown(56_000) == (56_000, 6_720, 62_720)


def test_rialit_fee_rounds_up_to_whole_toman() -> None:
    assert expected_rialit_payer_amount(50_001) == 56_002
