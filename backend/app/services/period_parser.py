import re
from datetime import date

def parse_period(period_str: str | None) -> tuple[date | None, date | None]:
    """
    Handles: 'FY25', 'FY 2024-25', 'FY2025', 'Q3 FY25', 'Q3 2025', 'March 2025', '2025'
    Indian fiscal year = April 1 to March 31. Returns (start_date, end_date).
    If unparseable, returns (None, None) — the original label is preserved separately.
    """
    if not period_str:
        return None, None

    text = period_str.strip().upper()

    # FY 2024-25 or FY24-25 -> starts April of the first year
    m = re.match(r"FY\s?(\d{2,4})-(\d{2,4})", text)
    if m:
        start_year = _normalize_year(m.group(1))
        return date(start_year, 4, 1), date(start_year + 1, 3, 31)

    # FY25 or FY2025 -> fiscal year ending March of that year
    m = re.match(r"FY\s?(\d{2,4})", text)
    if m:
        end_year = _normalize_year(m.group(1))
        return date(end_year - 1, 4, 1), date(end_year, 3, 31)

    # Q3 FY25 or Q3 2025 -> approximate quarter within fiscal year
    m = re.match(r"Q(\d)\s?(FY)?\s?(\d{2,4})", text)
    if m:
        quarter, _, year_raw = m.groups()
        year = _normalize_year(year_raw)
        fy_start_year = year - 1 if "FY" in text else year
        q_start_month = {"1": 4, "2": 7, "3": 10, "4": 1}[quarter]
        start_year = fy_start_year if quarter != "4" else fy_start_year + 1
        start = date(start_year, q_start_month, 1)
        end_month = q_start_month + 2
        end_year = start_year
        if end_month > 12:
            end_month -= 12
            end_year += 1
        end = date(end_year, end_month, 28)  # approximate, good enough for comparison purposes
        return start, end

    # Plain calendar year, e.g. "2025"
    m = re.match(r"^(\d{4})$", text)
    if m:
        year = int(m.group(1))
        return date(year, 1, 1), date(year, 12, 31)

    return None, None

def _normalize_year(y: str) -> int:
    y = int(y)
    return y if y > 100 else 2000 + y