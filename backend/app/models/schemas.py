from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class DocType(str, Enum):
    PITCH_DECK = "pitch_deck"
    FINANCIAL_STATEMENT = "financial_statement"
    CAP_TABLE = "cap_table"
    UNKNOWN = "unknown"

class ExtractedMetric(BaseModel):
    metric_name: str = Field(..., description="e.g. 'ARR', 'Monthly Burn Rate', 'Founder Equity %'")
    value: float
    unit: str = Field(..., description="e.g. 'INR', 'USD', 'percent', 'Cr', 'Lakh'")
    period: Optional[str] = Field(None, description="e.g. 'FY25', 'Q3 2025'")
    source_page: int
    raw_text: str = Field(..., description="The exact sentence/phrase this was extracted from")
    confidence: float = Field(..., ge=0, le=1)

class ExtractedClaim(BaseModel):
    """Non-numeric claims, e.g. 'we have 50 enterprise clients'"""
    claim_text: str
    category: Literal["traction", "market", "team", "product", "other"]
    source_page: int
    raw_text: str
    has_supporting_data: bool = Field(..., description="Does this doc itself show evidence, or is it asserted only")

class DocumentExtraction(BaseModel):
    filename: str
    doc_type: DocType
    metrics: list[ExtractedMetric]
    claims: list[ExtractedClaim]
    page_count: int
    ocr_used: bool