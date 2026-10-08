import re
from datetime import date

import jdatetime


_DATE_RE = re.compile(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$")


def jalali_to_gregorian(value: str) -> date:
    match = _DATE_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("فرمت تاریخ باید مانند 1405/01/15 باشد.")
    year, month, day = map(int, match.groups())
    try:
        return jdatetime.date(year, month, day).togregorian()
    except ValueError as exc:
        raise ValueError("تاریخ واردشده معتبر نیست.") from exc


def gregorian_display(value: date) -> str:
    return value.strftime("%Y/%m/%d")
