from app.models.schemas import DocumentExtraction, ExtractedMetric
from app.models.canonical_schemas import CanonicalMetric, SourceRef
from app.services.unit_parser import parse_unit
from app.services.period_parser import parse_period
from app.services.metric_aliases import normalize_metric_name

def canonicalize_metric(metric: ExtractedMetric, filename: str) -> CanonicalMetric:
    currency, scale, is_percent = parse_unit(metric.unit)
    normalized_value = metric.value * scale

    canonical_name, confidence = normalize_metric_name(metric.metric_name)
    period_start, period_end = parse_period(metric.period)

    return CanonicalMetric(
        canonical_name=canonical_name,
        name_match_confidence=confidence,
        value=normalized_value,
        currency=currency,
        is_percent=is_percent,
        period_label=metric.period or "unspecified",
        period_start=period_start,
        period_end=period_end,
        source=SourceRef(
            filename=filename,
            page=metric.source_page,
            raw_text=metric.raw_text,
            original_value=metric.value,
            original_unit=metric.unit,
        ),
    )

def canonicalize_extraction(extraction: DocumentExtraction) -> list[CanonicalMetric]:
    return [canonicalize_metric(m, extraction.filename) for m in extraction.metrics]