from app.models.canonical_schemas import CanonicalMetric
from app.models.consistency_schemas import ConsistencyReport
from app.models.risk_schemas import RiskAssessment
from app.services.risk_rules import (
    rule_metric_discrepancies,
    rule_unsupported_claims_ratio,
    rule_burn_exceeds_revenue,
    rule_low_runway,
)

def run_risk_assessment(
    metrics: list[CanonicalMetric],
    consistency: ConsistencyReport,
    total_claims: int,
) -> RiskAssessment:
    flags = []
    flags += rule_metric_discrepancies(consistency)
    flags += rule_unsupported_claims_ratio(consistency, total_claims)
    flags += rule_burn_exceeds_revenue(metrics)
    flags += rule_low_runway(metrics)

    return RiskAssessment(
        flags=flags,
        total_claims_checked=total_claims,
        unsupported_claims_count=len(consistency.unsupported_claims),
    )