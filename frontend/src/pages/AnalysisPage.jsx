import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "../context/SessionContext";
import "./AnalysisPage.css";

function groupMetrics(canonicalMetrics, consistency, risk) {
  const groups = {};
  for (const m of canonicalMetrics) {
    if (!groups[m.canonical_name]) groups[m.canonical_name] = [];
    groups[m.canonical_name].push(m);
  }

  return Object.entries(groups).map(([name, instances]) => {
    const discrepancy = consistency.discrepancies.find((d) => d.canonical_name === name);
    const relatedFlags = risk.flags.filter((f) =>
      f.description.includes(name) ||
      f.evidence.some((e) => instances.some((m) => m.source.filename === e.filename && m.source.page === e.page))
    );
    const unmatched = instances.some((m) => m.name_match_confidence < 0.85);

    let status = "consistent";
    if (discrepancy) status = "discrepancy";
    else if (unmatched) status = "unmatched";

    return { name, instances, status, discrepancy, relatedFlags };
  }).sort((a, b) => {
    const order = { discrepancy: 0, unmatched: 1, consistent: 2 };
    return order[a.status] - order[b.status];
  });
}

function buildClaims(extractions, consistency, risk) {
  const unsupportedRaw = new Set(consistency.unsupported_claims.map((c) => c.raw_text));
  const globalUnsupportedFlag = risk.flags.find((f) => f.rule_id === "UNSUPPORTED_CLAIMS_RATIO");

  return extractions.flatMap((ext) =>
    ext.claims.map((c) => ({
      claim_text: c.claim_text,
      category: c.category,
      filename: ext.filename,
      page: c.source_page,
      raw_text: c.raw_text,
      status: unsupportedRaw.has(c.raw_text) ? "unsupported" : "supported",
      relatedFlag: unsupportedRaw.has(c.raw_text) ? globalUnsupportedFlag : null,
    }))
  );
}

const STATUS_LABEL = { consistent: "Consistent", discrepancy: "Discrepancy", unmatched: "Unmatched", supported: "Supported", unsupported: "Unsupported" };

export default function AnalysisPage() {
  const { results } = useSession();
  const navigate = useNavigate();
  const [tab, setTab] = useState("metrics");
  const [openKey, setOpenKey] = useState(null);

  const metricGroups = useMemo(
    () => results ? groupMetrics(results.canonicalMetrics, results.consistency, results.risk) : [],
    [results]
  );
  const claims = useMemo(
    () => results ? buildClaims(results.extractions, results.consistency, results.risk) : [],
    [results]
  );

  if (!results) {
    return (
      <div className="analysis-empty">
        <p className="mono eyebrow">NO ACTIVE CASE FILE</p>
        <h2>Nothing to analyze yet</h2>
        <p>Upload documents in the Chat tab to build a metrics and claims breakdown.</p>
        <button className="cta" onClick={() => navigate("/chat")}>Go to Chat →</button>
      </div>
    );
  }

  const filenames = [...new Set(results.extractions.map((e) => e.filename))];

  return (
    <div className="analysis-page">
      <aside className="analysis-sidebar">
        <div className="sidebar-card">
          <div className="sidebar-card-header">
            <span>Documents</span>
          </div>
          <ul className="doc-list">
            {filenames.map((f) => (
              <li key={f}><span className="doc-icon">📄</span>{f}</li>
            ))}
          </ul>
          <div className="sidebar-status">
            <span className="status-dot" /> Processed
          </div>
        </div>

        <div className="sidebar-card">
          <div className="sidebar-card-header"><span>Overview</span></div>
          <div className="overview-row"><span>Metrics</span><span className="mono">{metricGroups.length}</span></div>
          <div className="overview-row"><span>Claims</span><span className="mono">{claims.length}</span></div>
          <div className="overview-row"><span>Discrepancies</span><span className="mono danger">{metricGroups.filter(g => g.status === "discrepancy").length}</span></div>
          <div className="overview-row"><span>Unsupported</span><span className="mono danger">{claims.filter(c => c.status === "unsupported").length}</span></div>
        </div>
      </aside>

      <main className="analysis-main">
        <div className="tab-toggle">
          <button className={tab === "metrics" ? "active" : ""} onClick={() => { setTab("metrics"); setOpenKey(null); }}>1. Metrics</button>
          <button className={tab === "claims" ? "active" : ""} onClick={() => { setTab("claims"); setOpenKey(null); }}>2. Claims</button>
        </div>

        {tab === "metrics" && (
          <div className="entry-list">
            {metricGroups.map((g) => (
              <div className={`entry-card status-${g.status}`} key={g.name}>
                <button className="entry-row" onClick={() => setOpenKey(openKey === g.name ? null : g.name)}>
                  <div className="entry-main">
                    <span className="entry-name">{g.name}</span>
                    <span className="entry-count mono">{g.instances.length} instance{g.instances.length > 1 ? "s" : ""}</span>
                  </div>
                  <span className={`status-pill status-${g.status}`}>{STATUS_LABEL[g.status]}</span>
                </button>

                {openKey === g.name && (
                  <div className="entry-detail">
                    {g.instances.map((m, i) => (
                      <div className="instance-row" key={i}>
                        <div className="instance-top">
                          <span className="mono instance-value">{m.value.toLocaleString()} {m.currency || (m.is_percent ? "%" : "")}</span>
                          <span className="mono instance-source">{m.source.filename} · p.{m.source.page}</span>
                        </div>
                        <p className="instance-sentence">"{m.source.raw_text}"</p>
                        <span className="mono instance-period">{m.period_label}</span>
                      </div>
                    ))}
                    {g.discrepancy && (
                      <p className="entry-note note-danger">
                        ⚠ {g.discrepancy.max_delta_percent}% delta detected across documents for this metric.
                      </p>
                    )}
                    {g.relatedFlags.length > 0 && (
                      <div className="entry-flags">
                        {g.relatedFlags.map((f, i) => (
                          <span key={i} className="mono flag-chip">{f.rule_name}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "claims" && (
          <div className="entry-list">
            {claims.map((c, idx) => (
              <div className={`entry-card status-${c.status}`} key={idx}>
                <button className="entry-row" onClick={() => setOpenKey(openKey === idx ? null : idx)}>
                  <div className="entry-main">
                    <span className="entry-name claim-name">{c.claim_text}</span>
                    <span className="entry-count mono">{c.category}</span>
                  </div>
                  <span className={`status-pill status-${c.status}`}>{STATUS_LABEL[c.status]}</span>
                </button>

                {openKey === idx && (
                  <div className="entry-detail">
                    <div className="instance-row">
                      <div className="instance-top">
                        <span className="mono instance-source">{c.filename} · p.{c.page}</span>
                      </div>
                      <p className="instance-sentence">"{c.raw_text}"</p>
                    </div>
                    {c.status === "unsupported" && (
                      <p className="entry-note note-danger">
                        ⚠ No supporting metric or corroborating statement found elsewhere in the uploaded documents.
                      </p>
                    )}
                    {c.relatedFlag && (
                      <div className="entry-flags">
                        <span className="mono flag-chip">{c.relatedFlag.rule_name}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}