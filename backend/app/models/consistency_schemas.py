from pydantic import BaseModel
from typing import Literal

class MetricValueRef(BaseModel):
    filename: str
    page: int
    value: float
    currency: str | None
    raw_text: str

class MetricDiscrepancy(BaseModel):
    canonical_name: str
    period_key: str
    values: list[MetricValueRef]
    max_delta_percent: float
    severity: Literal["low", "medium", "high"]

class UnsupportedClaim(BaseModel):
    claim_text: str
    category: str
    filename: str
    page: int
    raw_text: str

class ConsistencyReport(BaseModel):
    discrepancies: list[MetricDiscrepancy]
    unsupported_claims: list[UnsupportedClaim]