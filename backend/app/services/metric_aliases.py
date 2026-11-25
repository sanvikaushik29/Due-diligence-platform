from difflib import get_close_matches

CANONICAL_METRICS = [
    "ARR", "MRR", "Revenue", "Monthly Burn Rate", "Cash Runway",
    "Gross Margin", "EBITDA", "Operating Expenses", "Valuation",
    "Founder Equity %", "ESOP Pool %", "Customer Acquisition Cost",
    "Debt-to-Equity Ratio", "Cash Reserves",
    "User Projections", "Monthly Active Users", "Daily Active Users",
    "Funding Ask", "Amount Raised", "Net Promoter Score", "Retailer Pilots",
]

ALIASES = {
    "arr": "ARR", "annual recurring revenue": "ARR",
    "mrr": "MRR", "monthly recurring revenue": "MRR",
    "revenue": "Revenue", "total revenue": "Revenue", "net revenue": "Revenue",
    "burn rate": "Monthly Burn Rate", "burn rate: $": "Monthly Burn Rate",
    "monthly burn": "Monthly Burn Rate", "cash burn": "Monthly Burn Rate",
    "burn": "Monthly Burn Rate",
    "runway": "Cash Runway", "cash runway": "Cash Runway",
    "gross margin": "Gross Margin", "gm": "Gross Margin",
    "ebitda": "EBITDA",
    "opex": "Operating Expenses", "operating expenses": "Operating Expenses",
    "valuation": "Valuation", "post-money valuation": "Valuation",
    "pre-money valuation": "Valuation",
    "founder equity": "Founder Equity %", "founder ownership": "Founder Equity %",
    "esop": "ESOP Pool %", "esop pool": "ESOP Pool %",
    "cac": "Customer Acquisition Cost", "customer acquisition cost": "Customer Acquisition Cost",
    "debt to equity": "Debt-to-Equity Ratio", "d/e ratio": "Debt-to-Equity Ratio",
    "cash reserves": "Cash Reserves", "cash balance": "Cash Reserves",
    "cash on hand": "Cash Reserves",
    "projected users": "User Projections", "user projections": "User Projections",
    "users": "User Projections", "user base": "User Projections",
    "downloads": "User Projections",
    "mau": "Monthly Active Users", "monthly active users": "Monthly Active Users",
    "dau": "Daily Active Users", "daily active users": "Daily Active Users",
    "funding ask": "Funding Ask", "seed funding": "Funding Ask",
    "funding round": "Funding Ask", "seeking": "Funding Ask",
    "amount raised": "Amount Raised", "total raised": "Amount Raised",
    "capital raised": "Amount Raised",
    "nps": "Net Promoter Score", "net promoter score": "Net Promoter Score",
    "retailer pilots": "Retailer Pilots",
}

def normalize_metric_name(raw_name: str) -> tuple[str, float]:
    """Returns (canonical_name, confidence). Falls back to 'Uncategorized: X' if nothing matches well."""
    key = raw_name.lower().strip()

    if key in ALIASES:
        return ALIASES[key], 1.0

    close = get_close_matches(key, ALIASES.keys(), n=1, cutoff=0.75)
    if close:
        return ALIASES[close[0]], 0.85

    return f"Uncategorized: {raw_name}", 0.3