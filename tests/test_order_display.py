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
