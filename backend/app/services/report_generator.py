import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "reports_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=14, spaceAfter=10,
                               spaceBefore=18, textColor=colors.HexColor("#1a1a1a"),
                               fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SmallGray", fontSize=8, textColor=colors.gray))
    return styles

def _severity_color(severity: str):
    return {"high": colors.HexColor("#d9534f"), "medium": colors.HexColor("#f0ad4e"),
            "low": colors.HexColor("#5bc0de")}.get(severity, colors.gray)

def generate_report(
    company_name: str,
    extractions: list[dict],
    canonical_metrics: list[dict],
    consistency: dict,
    risk: dict,
    opening_summary: str,
) -> str:
    """Returns the file path of the generated PDF."""
    filename = f"{company_name.replace(' ', '_')}_due_diligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter,
                             topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = _styles()
    story = []

    # --- Title ---
    story.append(Paragraph(f"Due Diligence Report: {company_name}", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles["SmallGray"]))
    story.append(Spacer(1, 0.3*inch))

    # --- 1. Executive Summary ---
    story.append(Paragraph("1. Executive Summary", styles["SectionHeader"]))
    story.append(Paragraph(opening_summary, styles["BodyText"]))

    # --- 2. Extracted Metrics (canonicalized) ---
    story.append(Paragraph("2. Extracted Metrics", styles["SectionHeader"]))
    metric_rows = [["Metric", "Value", "Period", "Source", "Page", "Match"]]
    for m in canonical_metrics:
        confidence_tag = "OK" if m["name_match_confidence"] >= 0.85 else "?"
        unit_label = m.get("currency") or ("%" if m["is_percent"] else "")
        metric_rows.append([
            m["canonical_name"],
            f"{m['value']:,.2f} {unit_label}".strip(),
            m["period_label"],
            m["source"]["filename"],
            str(m["source"]["page"]),
            confidence_tag,
        ])
    if len(metric_rows) > 1:
        table = Table(metric_rows, repeatRows=1,
                       colWidths=[1.7*inch, 1.2*inch, 0.8*inch, 1.5*inch, 0.4*inch, 0.4*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No structured metrics were extracted.", styles["BodyText"]))

    # --- 3. Cross-Document Discrepancies ---
    story.append(Paragraph("3. Cross-Document Discrepancies", styles["SectionHeader"]))
    discrepancies = consistency.get("discrepancies", [])
    if not discrepancies:
        story.append(Paragraph("No cross-document discrepancies detected.", styles["BodyText"]))
    else:
        for d in discrepancies:
            color = _severity_color(d["severity"])
            story.append(Paragraph(
                f'<font color="{color.hexval()}"><b>[{d["severity"].upper()}]</b></font> '
                f'{d["canonical_name"]} — {d["max_delta_percent"]}% delta ({d["period_key"]})',
                styles["BodyText"]
            ))
            for v in d["values"]:
                story.append(Paragraph(
                    f'&nbsp;&nbsp;• {v["filename"]} (p.{v["page"]}): {v["value"]:,.2f} — "{v["raw_text"]}"',
                    styles["SmallGray"]
                ))
            story.append(Spacer(1, 0.1*inch))

    # --- 4. Risk Flags ---
    story.append(Paragraph("4. Risk Flags", styles["SectionHeader"]))
    flags = risk.get("flags", [])
    if not flags:
        story.append(Paragraph("No risk rules were triggered.", styles["BodyText"]))
    else:
        for f in flags:
            color = _severity_color(f["severity"])
            story.append(Paragraph(
                f'<font color="{color.hexval()}"><b>[{f["severity"].upper()}]</b></font> '
                f'{f["rule_name"]}: {f["description"]}',
                styles["BodyText"]
            ))
            story.append(Spacer(1, 0.08*inch))

    # --- 5. Unsupported Claims ---
    story.append(Paragraph("5. Claims Without Supporting Data", styles["SectionHeader"]))
    unsupported = consistency.get("unsupported_claims", [])
    if not unsupported:
        story.append(Paragraph("All claims were backed by supporting data.", styles["BodyText"]))
    else:
        for c in unsupported:
            story.append(Paragraph(
                f'• [{c["category"]}] {c["claim_text"]} ({c["filename"]}, p.{c["page"]})',
                styles["BodyText"]
            ))

    # --- 6. Data Gaps ---
    story.append(PageBreak())
    story.append(Paragraph("6. Data Gaps", styles["SectionHeader"]))
    story.append(Paragraph(
        "The following limitations apply to this analysis: metrics reported with vague or "
        "relative time periods (e.g. \"Year 1\") could not be cross-referenced against metrics "
        "using absolute calendar periods, and were excluded from discrepancy detection rather "
        "than compared under an assumed mapping. Metrics marked '?' in the Match column above "
        "were not confidently recognized against the standard metric dictionary and should be "
        "reviewed manually.",
        styles["BodyText"]
    ))

    # --- 7. Appendix ---
    story.append(PageBreak())
    story.append(Paragraph("7. Appendix — All Extracted Claims", styles["SectionHeader"]))
    for ext in extractions:
        story.append(Paragraph(f"<b>{ext['filename']}</b>", styles["BodyText"]))
        for c in ext.get("claims", []):
            story.append(Paragraph(
                f'• [{c["category"]}] {c["claim_text"]} (p.{c["source_page"]})',
                styles["SmallGray"]
            ))
        story.append(Spacer(1, 0.15*inch))

    doc.build(story)
    return filepath