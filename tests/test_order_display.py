from app.bot.handlers import format_optional_order_details


def test_optional_order_details_use_real_line_breaks_and_escape_user_text():
    rendered = format_optional_order_details(
        {
            "province": "اصفهان",
            "city": "اصفهان",
            "child_count": "2",
            "service_description": "<متن مشترک>",
        }
    )

    assert rendered == (
        "\nاستان: اصفهان"
        "\nشهر: اصفهان"
        "\nتعداد دانش‌آموزان ثبت‌شده: 2"
        "\n\n📝 توضیحات مشترک: &lt;متن مشترک&gt;"
    )
    assert r"\n" not in rendered



def test_screening_fee_is_calculated_per_student():
    from app.bot.handlers import screening_total_amount

    assert screening_total_amount(400, 1) == 400
    assert screening_total_amount(400, 2) == 800
    assert screening_total_amount(400, 3) == 1200
    assert screening_total_amount(2500, 4) == 10000


def test_screening_fee_rejects_invalid_price_or_student_count():
    import pytest
    from app.bot.handlers import screening_total_amount

    with pytest.raises(ValueError):
        screening_total_amount(0, 1)
    with pytest.raises(ValueError):
        screening_total_amount(400, 0)


def test_screening_order_stores_total_and_per_student_snapshot():
    from pathlib import Path

    source = Path("app/bot/handlers.py").read_text(encoding="utf-8")
    save_block = source.split("async def save_order_data", 1)[1].split("async def save_receipt", 1)[0]
    summary_block = source.split("async def show_additional_summary", 1)[1].split("async def additional_service_confirm", 1)[0]
    assert "order.price_snapshot_toman = total" in save_block
    assert 'payload["screening_unit_price_toman"] = unit_price' in save_block
    assert 'payload["screening_total_toman"] = total' in save_block
    assert "هزینه هر دانش‌آموز" in summary_block
    assert "مجموع هزینه" in summary_block
