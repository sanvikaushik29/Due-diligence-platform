from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import shutil
import os
from fastapi import HTTPException
from app.services.session_store import save_session, list_sessions, get_session, delete_session
from app.services.pdf_parser import extract_pages
from app.services.ocr import ocr_page
from app.services.extractor import classify_doc_type, extract_page
from app.services.canonicalizer import canonicalize_extraction
from app.services.consistency_engine import (
    detect_metric_discrepancies,
    collect_unsupported_claims,
)
from app.services.risk_engine import run_risk_assessment
from app.services.vector_store import index_session
from app.services.chat_engine import (
    answer_query,
    generate_opening_summary,
)
from app.services.report_generator import generate_report

from app.models.schemas import (
    DocumentExtraction,
    ExtractedMetric,
    ExtractedClaim,
    DocType,
)
from app.models.canonical_schemas import CanonicalMetric
from app.models.consistency_schemas import ConsistencyReport
from app.models.risk_schemas import RiskAssessment
from app.models.chat_schemas import (
    IndexRequest,
    ChatRequest,
    ChatResponse,
    OpeningSummaryRequest,
)

router = APIRouter()


class ConsistencyCheckRequest(BaseModel):
    metrics: list[CanonicalMetric] = []
    extractions: list[DocumentExtraction] = []


class OpeningSummaryDirectRequest(BaseModel):
    risk: dict
    consistency: dict


class ReportRequest(BaseModel):
    company_name: str
    extractions: list[dict]
    canonical_metrics: list[dict]
    consistency: dict
    risk: dict
    opening_summary: str


@router.post("/documents/extract")
async def extract_document(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    pages = extract_pages(tmp_path)
    ocr_used = False

    for p in pages:
        if p["needs_ocr"] and p["image_bytes"]:
            p["text"] = ocr_page(p["image_bytes"])
            ocr_used = True

    doc_type = classify_doc_type(pages[0]["text"]) if pages else DocType.UNKNOWN

    all_metrics = []
    all_claims = []

    for p in pages:
        if not p["text"].strip():
            continue

        result = extract_page(
            p["text"],
            doc_type,
            p["page_number"],
        )

        for m in result.get("metrics", []):
            all_metrics.append(
                ExtractedMetric(
                    **m,
                    source_page=p["page_number"],
                )
            )

        for c in result.get("claims", []):
            all_claims.append(
                ExtractedClaim(
                    **c,
                    source_page=p["page_number"],
                )
            )

    extraction = DocumentExtraction(
        filename=file.filename,
        doc_type=doc_type,
        metrics=all_metrics,
        claims=all_claims,
        page_count=len(pages),
        ocr_used=ocr_used,
    )

    return extraction.model_dump()


@router.post("/documents/canonicalize")
async def canonicalize(extraction: DocumentExtraction):
    canonical = canonicalize_extraction(extraction)
    return [c.model_dump() for c in canonical]


@router.post(
    "/documents/consistency-check",
    response_model=ConsistencyReport,
)
async def consistency_check(payload: ConsistencyCheckRequest):
    discrepancies = detect_metric_discrepancies(payload.metrics)
    unsupported = collect_unsupported_claims(payload.extractions)

    return ConsistencyReport(
        discrepancies=discrepancies,
        unsupported_claims=unsupported,
    )


@router.post(
    "/documents/risk-assessment",
    response_model=RiskAssessment,
)
async def risk_assessment(payload: ConsistencyCheckRequest):
    consistency_report = ConsistencyReport(
        discrepancies=detect_metric_discrepancies(payload.metrics),
        unsupported_claims=collect_unsupported_claims(payload.extractions),
    )

    total_claims = sum(len(ext.claims) for ext in payload.extractions)

    return run_risk_assessment(
        payload.metrics,
        consistency_report,
        total_claims,
    )


@router.post("/documents/generate-report")
async def generate_report_route(payload: ReportRequest):
    filepath = generate_report(
        company_name=payload.company_name,
        extractions=payload.extractions,
        canonical_metrics=payload.canonical_metrics,
        consistency=payload.consistency,
        risk=payload.risk,
        opening_summary=payload.opening_summary,
    )
    return FileResponse(filepath, media_type="application/pdf",
                         filename=os.path.basename(filepath))


@router.post("/chat/index")
async def chat_index(payload: IndexRequest):
    count = index_session(
        payload.session_id,
        payload.extractions,
        payload.metrics,
        payload.consistency,
        payload.risk,
    )

    return {
        "indexed_chunks": count
    }


@router.post("/chat/query", response_model=ChatResponse)
async def chat_query(payload: ChatRequest):
    answer, citations = answer_query(
        payload.session_id,
        payload.message,
        [h.model_dump() for h in payload.history],
    )

    return ChatResponse(
        answer=answer,
        citations=citations,
    )


@router.post("/chat/opening-summary")
async def opening_summary(payload: OpeningSummaryRequest):
    return {
        "note": "use /chat/opening-summary-direct for now, see testing steps"
    }


@router.post("/chat/opening-summary-direct")
async def opening_summary_direct(payload: OpeningSummaryDirectRequest):
    summary = generate_opening_summary(
        payload.risk,
        payload.consistency,
    )

    return {
        "summary": summary
    }

class SaveSessionRequest(BaseModel):
    session_id: str
    company_name: str
    extractions: list[dict]
    canonical_metrics: list[dict]
    consistency: dict
    risk: dict
    summary: str

@router.post("/sessions/save")
async def save_session_route(payload: SaveSessionRequest):
    save_session(payload.session_id, payload.company_name, payload.extractions,
                 payload.canonical_metrics, payload.consistency, payload.risk, payload.summary)
    return {"status": "saved"}

@router.get("/sessions")
async def list_sessions_route():
    return list_sessions()

@router.get("/sessions/{session_id}")
async def get_session_route(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
async def delete_session_route(session_id: str):
    delete_session(session_id)
    return {"status": "deleted"}