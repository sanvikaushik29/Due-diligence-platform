import re

SCALE_MAP = {
    "cr": 1e7, "crore": 1e7, "crores": 1e7,
    "lakh": 1e5, "lac": 1e5, "lakhs": 1e5,
    "k": 1e3, "thousand": 1e3,
    "m": 1e6, "mn": 1e6, "million": 1e6,
    "bn": 1e9, "billion": 1e9,
}

CURRENCY_MAP = {
    "inr": "INR", "rs": "INR", "rs.": "INR", "₹": "INR", "rupees": "INR",
    "usd": "USD", "$": "USD", "dollars": "USD",
}

def parse_unit(unit_str: str) -> tuple[str | None, float, bool]:
    """
    Returns (currency_code_or_None, scale_multiplier, is_percent)
    e.g. "INR Cr" -> ("INR", 1e7, False)
         "percent" -> (None, 1.0, True)
         "USD" -> ("USD", 1.0, False)
    """
    if not unit_str:
        return None, 1.0, False

    text = unit_str.lower().strip()

    if "%" in text or "percent" in text:
        return None, 1.0, True

    currency = None
    for key, code in CURRENCY_MAP.items():
        if re.search(rf"\b{re.escape(key)}\b", text):
            currency = code
            break
    scale = 1.0
    for key, mult in SCALE_MAP.items():
        # word-boundary match so "m" doesn't match inside "million" twice, etc.
        if re.search(rf"\b{re.escape(key)}\b", text):
            scale = mult
            break

    return currency, scale, False