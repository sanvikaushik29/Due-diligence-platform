from pydantic import BaseModel
from typing import Literal

class RiskEvidence(BaseModel):
    filename: str
    page: int
    raw_text: str
    value: float | None = None

class RiskFlag(BaseModel):
    rule_id: str
    rule_name: str
    category: Literal["financial", "business", "operational", "consistency"]
    severity: Literal["low", "medium", "high"]
    description: str
    evidence: list[RiskEvidence]

class RiskAssessment(BaseModel):
    flags: list[RiskFlag]
    total_claims_checked: int
    unsupported_claims_count: int