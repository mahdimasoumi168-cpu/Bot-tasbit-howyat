from app.utils.dates import gregorian_display,jalali_to_gregorian

def test_jalali_conversion():
    assert gregorian_display(jalali_to_gregorian("1405/01/10"))=="2026/03/30"

def test_invalid_date():
    try:jalali_to_gregorian("1405/13/01")
    except ValueError:pass
    else:raise AssertionError("Expected invalid Jalali date")
