from app.models.canonical_schemas import CanonicalMetric
from app.models.consistency_schemas import ConsistencyReport
from app.models.risk_schemas import RiskFlag, RiskEvidence

# ---- Rule 1: Cross-document metric discrepancies ----
def rule_metric_discrepancies(consistency: ConsistencyReport) -> list[RiskFlag]:
    flags = []
    for d in consistency.discrepancies:
        if d.severity == "low":
            continue  # low-severity deltas are noise, not worth flagging as risk
        flags.append(RiskFlag(
            rule_id="DISCREPANCY_" + d.canonical_name.upper().replace(" ", "_"),
            rule_name="Cross-Document Discrepancy",
            category="consistency",
            severity=d.severity,
            description=(
                f"{d.canonical_name} differs by {d.max_delta_percent}% across documents "
                f"for period '{d.period_key}'."
            ),
            evidence=[
                RiskEvidence(filename=v.filename, page=v.page, raw_text=v.raw_text, value=v.value)
                for v in d.values
            ],
        ))
    return flags

# ---- Rule 2: High proportion of unsupported claims ----
def rule_unsupported_claims_ratio(
    consistency: ConsistencyReport, total_claims: int, threshold: float = 0.5
) -> list[RiskFlag]:
    if total_claims == 0:
        return []
    unsupported_count = len(consistency.unsupported_claims)
    ratio = unsupported_count / total_claims
    if ratio < threshold:
        return []

    severity = "high" if ratio >= 0.75 else "medium"
    return [RiskFlag(
        rule_id="UNSUPPORTED_CLAIMS_RATIO",
        rule_name="High Proportion of Unsupported Claims",
        category="business",
        severity=severity,
        description=(
            f"{unsupported_count} of {total_claims} claims ({ratio:.0%}) have no supporting "
            f"data anywhere in the uploaded documents."
        ),
        evidence=[
            RiskEvidence(filename=c.filename, page=c.page, raw_text=c.raw_text)
            for c in consistency.unsupported_claims[:5]  # cap evidence list, avoid huge payloads
        ],
    )]

# ---- Rule 3: Burn rate high relative to revenue ----
def rule_burn_exceeds_revenue(metrics: list[CanonicalMetric]) -> list[RiskFlag]:
    burn = _latest(metrics, "Monthly Burn Rate")
    revenue = _latest(metrics, "Revenue") or _latest(metrics, "ARR")
    if not burn or not revenue or revenue.value == 0:
        return []  # can't evaluate without both — don't guess

    annualized_burn = burn.value * 12
    if annualized_burn <= revenue.value:
        return []

    ratio = annualized_burn / revenue.value
    severity = "high" if ratio >= 2 else "medium"
    return [RiskFlag(
        rule_id="BURN_EXCEEDS_REVENUE",
        rule_name="Burn Rate Exceeds Annualized Revenue",
        category="financial",
        severity=severity,
        description=(
            f"Annualized burn (${annualized_burn:,.0f}) exceeds reported revenue "
            f"(${revenue.value:,.0f}) by {ratio:.1f}x."
        ),
        evidence=[
            RiskEvidence(filename=burn.source.filename, page=burn.source.page,
                         raw_text=burn.source.raw_text, value=burn.value),
            RiskEvidence(filename=revenue.source.filename, page=revenue.source.page,
                         raw_text=revenue.source.raw_text, value=revenue.value),
        ],
    )]

# ---- Rule 4: Cash runway under 6 months ----
def rule_low_runway(metrics: list[CanonicalMetric], threshold_months: int = 6) -> list[RiskFlag]:
    cash = _latest(metrics, "Cash Reserves")
    burn = _latest(metrics, "Monthly Burn Rate")
    if not cash or not burn or burn.value == 0:
        return []

    runway_months = cash.value / burn.value
    if runway_months >= threshold_months:
        return []

    severity = "high" if runway_months < 3 else "medium"
    return [RiskFlag(
        rule_id="LOW_CASH_RUNWAY",
        rule_name="Cash Runway Below Threshold",
        category="financial",
        severity=severity,
        description=f"Estimated runway is {runway_months:.1f} months at current burn rate.",
        evidence=[
            RiskEvidence(filename=cash.source.filename, page=cash.source.page,
                         raw_text=cash.source.raw_text, value=cash.value),
            RiskEvidence(filename=burn.source.filename, page=burn.source.page,
                         raw_text=burn.source.raw_text, value=burn.value),
        ],
    )]

# ---- helper ----
def _latest(metrics: list[CanonicalMetric], name: str) -> CanonicalMetric | None:
    """Picks the metric with the latest period_end if duplicates exist, else first match."""
    matches = [m for m in metrics if m.canonical_name == name]
    if not matches:
        return None
    dated = [m for m in matches if m.period_end]
    if dated:
        return max(dated, key=lambda m: m.period_end)
    return matches[0]