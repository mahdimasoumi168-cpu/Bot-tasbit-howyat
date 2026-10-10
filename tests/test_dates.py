from app.utils.dates import gregorian_display, jalali_to_gregorian


def test_jalali_conversion():
    assert gregorian_display(jalali_to_gregorian("1405/01/10")) == "2026/03/30"


def test_invalid_month():
    try:
        jalali_to_gregorian("1405/13/01")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid Jalali date")


def test_jalali_persian_digits():
    assert gregorian_display(jalali_to_gregorian("۱۴۰۵/۰۱/۱۰")) == "2026/03/30"


def test_jalali_arabic_digits_and_hyphens():
    assert gregorian_display(jalali_to_gregorian("١٤٠٥-٠١-١٠")) == "2026/03/30"


def test_invalid_day_is_rejected():
    try:
        jalali_to_gregorian("1405/01/32")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid Jalali day")


def test_invalid_format_is_rejected():
    for value in ("", "1405.01.10", "1405/1", "10/01/1405"):
        try:
            jalali_to_gregorian(value)
        except ValueError:
            continue
        raise AssertionError(f"Expected invalid date format to be rejected: {value!r}")
