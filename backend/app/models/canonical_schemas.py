from pydantic import BaseModel
from typing import Optional
from datetime import date

class SourceRef(BaseModel):
    filename: str
    page: int
    raw_text: str
    original_value: float
    original_unit: str

class CanonicalMetric(BaseModel):
    canonical_name: str          # e.g. "ARR", or "Uncategorized: <original>" if no match found
    name_match_confidence: float # 1.0 = dictionary match, <1.0 = fuzzy/LLM match
    value: float                 # normalized, scale multiplier applied (no more "Cr"/"Lakh")
    currency: Optional[str]      # "INR", "USD", or None for percentages/ratios
    is_percent: bool
    period_label: str            # original label kept for display, e.g. "FY25"
    period_start: Optional[date]
    period_end: Optional[date]
    source: SourceRef