from pydantic import BaseModel
from typing import Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class IndexRequest(BaseModel):
    session_id: str
    extractions: list  # list[DocumentExtraction] dicts
    metrics: list      # list[CanonicalMetric] dicts
    consistency: dict  # ConsistencyReport dict
    risk: dict         # RiskAssessment dict

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: list[ChatMessage] = []

class Citation(BaseModel):
    filename: str
    page: int
    raw_text: str

class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]

class OpeningSummaryRequest(BaseModel):
    session_id: str