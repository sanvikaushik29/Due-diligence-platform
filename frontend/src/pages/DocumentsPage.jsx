import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "../context/SessionContext";
import "./DocumentsPage.css";

const CATEGORIES = ["market", "product", "team", "traction", "other"];
const CATEGORY_LABEL = {
  market: "Market", product: "Product", team: "Team",
  traction: "Traction", other: "Other / Financial",
};

function analyzeDocument(ext, canonicalMetrics, consistency) {
  const claims = ext.claims;
  const unsupported = claims.filter((c) => !c.has_supporting_data);
  const supportedRatio = claims.length ? 1 - unsupported.length / claims.length : 0;

  const presentCategories = new Set(claims.map((c) => c.category));
  const missingSections = CATEGORIES.filter((c) => !presentCategories.has(c));

  const docMetrics = canonicalMetrics.filter((m) => m.source.filename === ext.filename);
  const matchedMetrics = docMetrics.filter((m) => m.name_match_confidence >= 0.85);

  const involvedDiscrepancies = consistency.discrepancies.filter((d) =>
    d.values.some((v) => v.filename === ext.filename)
  );

  // Simple, transparent completeness score — not a hidden black box.
  // Weighted: section coverage (40%), evidence support (35%), metric density (25%)
  const sectionScore = (CATEGORIES.length - missingSections.length) / CATEGORIES.length;
  const metricScore = Math.min(1, docMetrics.length / 10);
  const completeness = Math.round((sectionScore * 0.4 + supportedRatio * 0.35 + metricScore * 0.25) * 100);

  return {
    filename: ext.filename,
    pageCount: ext.page_count,
    ocrUsed: ext.ocr_used,
    docType: ext.doc_type,
    claimsCount: claims.length,
    unsupportedCount: unsupported.length,
    supportedRatio,
    missingSections,
    metricsCount: docMetrics.length,
    matchedMetricsCount: matchedMetrics.length,
    discrepancyCount: involvedDiscrepancies.length,
    completeness,
  };
}

export default function DocumentsPage() {
  const { results } = useSession();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(null);
  const [compareA, setCompareA] = useState("");
  const [compareB, setCompareB] = useState("");

  const docStats = useMemo(() => {
    if (!results) return [];
    return results.extractions.map((ext) =>
      analyzeDocument(ext, results.canonicalMetrics, results.consistency)
    );
  }, [results]);

  if (!results) {
    return (
      <div className="docs-empty">
        <p className="mono eyebrow">NO ACTIVE CASE FILE</p>
        <h2>No documents uploaded yet</h2>
        <p>Upload a data room in the Chat tab to see it here.</p>
        <button className="cta" onClick={() => navigate("/chat")}>Go to Chat →</button>
      </div>
    );
  }

  const statA = docStats.find((d) => d.filename === compareA);
  const statB = docStats.find((d) => d.filename === compareB);

  return (
    <div className="docs-page">
      <div className="docs-header">
        <div>
          <p className="mono eyebrow">DATA ROOM</p>
          <h2>{results.companyName}</h2>
        </div>
        <span className="doc-total mono">{docStats.length} document{docStats.length !== 1 ? "s" : ""} · Processed</span>
      </div>

      <div className="doc-list-block">
        {docStats.map((d) => (
          <div className="doc-card" key={d.filename}>
            <button className="doc-card-row" onClick={() => setExpanded(expanded === d.filename ? null : d.filename)}>
              <div className="doc-card-main">
                <span className="doc-file-icon">📄</span>
                <div>
                  <p className="doc-filename">{d.filename}</p>
                  <p className="doc-meta mono">{d.pageCount} pages · {d.docType.replace("_", " ")}{d.ocrUsed ? " · OCR" : ""}</p>
                </div>
              </div>
              <div className="doc-card-stats">
                <span className="mini-stat"><b>{d.metricsCount}</b> metrics</span>
                <span className="mini-stat"><b>{d.claimsCount}</b> claims</span>
                <span className={`mini-stat ${d.unsupportedCount > 0 ? "warn" : ""}`}><b>{d.unsupportedCount}</b> unsupported</span>
                <span className="completeness-badge mono">{d.completeness}% complete</span>
              </div>
            </button>

            {expanded === d.filename && (
              <div className="doc-card-detail">
                <div className="detail-row">
                  <span>Metrics matched to standard dictionary</span>
                  <span className="mono">{d.matchedMetricsCount} / {d.metricsCount}</span>
                </div>
                <div className="detail-row">
                  <span>Evidence support ratio</span>
                  <span className="mono">{Math.round(d.supportedRatio * 100)}%</span>
                </div>
                <div className="detail-row">
                  <span>Involved in cross-document discrepancies</span>
                  <span className={`mono ${d.discrepancyCount > 0 ? "danger" : ""}`}>{d.discrepancyCount}</span>
                </div>
                <div className="detail-row">
                  <span>Sections not covered</span>
                  <span className="mono">
                    {d.missingSections.length === 0 ? "None" : d.missingSections.map(CATEGORY_LABEL_LOOKUP).join(", ")}
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <section className="compare-section">
        <h3>Compare Documents</h3>
        <p className="compare-sub">
          An objective, evidence-based breakdown — not a recommendation on which to invest in.
        </p>

        <div className="compare-selectors">
          <select value={compareA} onChange={(e) => setCompareA(e.target.value)}>
            <option value="">Select document A</option>
            {docStats.map((d) => <option key={d.filename} value={d.filename}>{d.filename}</option>)}
          </select>
          <span className="vs mono">VS</span>
          <select value={compareB} onChange={(e) => setCompareB(e.target.value)}>
            <option value="">Select document B</option>
            {docStats.map((d) => <option key={d.filename} value={d.filename}>{d.filename}</option>)}
          </select>
        </div>

        {statA && statB && statA.filename !== statB.filename && (
          <div className="compare-table">
            <CompareRow label="Completeness" a={`${statA.completeness}%`} b={`${statB.completeness}%`} winner={statA.completeness === statB.completeness ? null : statA.completeness > statB.completeness ? "a" : "b"} />
            <CompareRow label="Evidence support ratio" a={`${Math.round(statA.supportedRatio * 100)}%`} b={`${Math.round(statB.supportedRatio * 100)}%`} winner={statA.supportedRatio === statB.supportedRatio ? null : statA.supportedRatio > statB.supportedRatio ? "a" : "b"} />
            <CompareRow label="Metrics extracted" a={statA.metricsCount} b={statB.metricsCount} winner={statA.metricsCount === statB.metricsCount ? null : statA.metricsCount > statB.metricsCount ? "a" : "b"} />
            <CompareRow label="Unsupported claims" a={statA.unsupportedCount} b={statB.unsupportedCount} winner={statA.unsupportedCount === statB.unsupportedCount ? null : statA.unsupportedCount < statB.unsupportedCount ? "a" : "b"} lowerBetter />
            <CompareRow label="Involved in discrepancies" a={statA.discrepancyCount} b={statB.discrepancyCount} winner={statA.discrepancyCount === statB.discrepancyCount ? null : statA.discrepancyCount < statB.discrepancyCount ? "a" : "b"} lowerBetter />
            <CompareRow
              label="Missing sections"
              a={statA.missingSections.length === 0 ? "None" : statA.missingSections.map(CATEGORY_LABEL_LOOKUP).join(", ")}
              b={statB.missingSections.length === 0 ? "None" : statB.missingSections.map(CATEGORY_LABEL_LOOKUP).join(", ")}
              winner={statA.missingSections.length === statB.missingSections.length ? null : statA.missingSections.length < statB.missingSections.length ? "a" : "b"}
              lowerBetter
            />
          </div>
        )}

        {statA && statB && statA.filename === statB.filename && (
          <p className="compare-hint">Select two different documents to compare.</p>
        )}
      </section>
    </div>
  );
}

function CATEGORY_LABEL_LOOKUP(cat) { return CATEGORY_LABEL[cat] || cat; }

function CompareRow({ label, a, b, winner, lowerBetter }) {
  return (
    <div className="compare-row">
      <span className={`compare-cell ${winner === "a" ? "winner" : ""}`}>{a}</span>
      <span className="compare-label">{label}</span>
      <span className={`compare-cell ${winner === "b" ? "winner" : ""}`}>{b}</span>
    </div>
  );
}