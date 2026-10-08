import re
from datetime import date
import jdatetime

_DATE_RE=re.compile(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$")

def _normalize_digits(value:str)->str:
    table=str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789")
    return value.translate(table)

def jalali_to_gregorian(value:str)->date:
    normalized=_normalize_digits(value.strip())
    match=_DATE_RE.fullmatch(normalized)
    if not match: raise ValueError("فرمت تاریخ باید مانند ۱۴۰۵/۰۱/۱۵ باشد.")
    year,month,day=map(int,match.groups())
    try:return jdatetime.date(year,month,day).togregorian()
    except ValueError as exc:raise ValueError("تاریخ واردشده معتبر نیست.") from exc

def gregorian_display(value:date)->str:
    return value.strftime("%Y/%m/%d")
