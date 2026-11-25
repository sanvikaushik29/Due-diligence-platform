from app.models.canonical_schemas import CanonicalMetric
from app.models.schemas import DocumentExtraction
from app.models.consistency_schemas import MetricDiscrepancy, MetricValueRef, UnsupportedClaim

DEFAULT_THRESHOLD_PERCENT = 10.0
MIN_CONFIDENCE_TO_COMPARE = 0.5  # skip "Uncategorized"/low-confidence matches — too unreliable to compare

def _group_key(m: CanonicalMetric) -> tuple[str, str]:
    if m.period_start and m.period_end:
        period_key = f"{m.period_start.isoformat()}_{m.period_end.isoformat()}"
    else:
        period_key = m.period_label
    return (m.canonical_name, period_key)

def detect_metric_discrepancies(
    metrics: list[CanonicalMetric],
    threshold_percent: float = DEFAULT_THRESHOLD_PERCENT,
) -> list[MetricDiscrepancy]:
    groups: dict[tuple[str, str], list[CanonicalMetric]] = {}
    for m in metrics:
        if m.name_match_confidence < MIN_CONFIDENCE_TO_COMPARE:
            continue
        groups.setdefault(_group_key(m), []).append(m)

    discrepancies = []
    for (canonical_name, period_key), group in groups.items():
        distinct_files = {m.source.filename for m in group}
        if len(distinct_files) < 2:
            continue  # need at least 2 different documents to call it a "discrepancy"

        values = [m.value for m in group]
        max_v, min_v = max(values), min(values)
        if min_v == 0:
            continue  # avoid divide-by-zero; a metric legitimately at 0 vs non-zero is worth a separate check later

        delta_percent = ((max_v - min_v) / min_v) * 100
        if delta_percent < threshold_percent:
            continue

        severity = "high" if delta_percent >= 50 else "medium" if delta_percent >= 20 else "low"

        discrepancies.append(MetricDiscrepancy(
            canonical_name=canonical_name,
            period_key=period_key,
            values=[
                MetricValueRef(
                    filename=m.source.filename,
                    page=m.source.page,
                    value=m.value,
                    currency=m.currency,
                    raw_text=m.source.raw_text,
                ) for m in group
            ],
            max_delta_percent=round(delta_percent, 1),
            severity=severity,
        ))

    return discrepancies

def collect_unsupported_claims(extractions: list[DocumentExtraction]) -> list[UnsupportedClaim]:
    result = []
    for ext in extractions:
        for c in ext.claims:
            if not c.has_supporting_data:
                result.append(UnsupportedClaim(
                    claim_text=c.claim_text,
                    category=c.category,
                    filename=ext.filename,
                    page=c.source_page,
                    raw_text=c.raw_text,
                ))
    return result