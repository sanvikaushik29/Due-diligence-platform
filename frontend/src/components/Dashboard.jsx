import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import StampBadge from "./StampBadge";
import { generateReport } from "../api";
import "./Dashboard.css";

const SEVERITY_COLOR = { high: "#E0553B", medium: "#E0B255", low: "#5FBE8B" };
const AXIS_TICK = { fontSize: 11, fontFamily: "IBM Plex Mono", fill: "#8A9690" };
const TOOLTIP_STYLE = { background: "#1B231F", border: "1px solid #2A332E", color: "#EDEAE0", fontSize: 12 };

function computeStats(results) {
  const { extractions, canonicalMetrics, consistency, risk } = results;
  const claimsExtracted = extractions.reduce((n, e) => n + e.claims.length, 0);
  const uniqueMetrics = new Set(canonicalMetrics.map((m) => m.canonical_name)).size;
  const unsupported = consistency.unsupported_claims.length;
  const avgConfidence = canonicalMetrics.length
    ? canonicalMetrics.reduce((s, m) => s + m.name_match_confidence, 0) / canonicalMetrics.length
    : 0;

  return [
    { label: "Documents", value: extractions.length },
    { label: "Claims Extracted", value: claimsExtracted },
    { label: "Metrics Found", value: uniqueMetrics },
    { label: "Unsupported Claims", value: unsupported, sub: claimsExtracted ? `${Math.round((unsupported / claimsExtracted) * 100)}% of total` : "", warn: true },
    { label: "Discrepancies", value: consistency.discrepancies.length, danger: consistency.discrepancies.length > 0 },
    { label: "Risk Rules Triggered", value: risk.flags.length, sub: risk.flags.some(f=>f.severity==="high") ? "High present" : "High / Medium" },
    { label: "Confidence Level", value: `${Math.round(avgConfidence * 100)}%`, good: true },
  ];
}

const AREA_METRIC_MAP = {
  Revenue: ["Revenue", "ARR", "MRR"],
  Funding: ["Funding Ask", "Amount Raised"],
  Runway: ["Cash Runway", "Cash Reserves", "Monthly Burn Rate"],
};
const AREA_CLAIM_CATEGORY_MAP = { "Team & Hiring": "team", Market: "market", Product: "product" };

function computeRiskHeatmap(results) {
  const { canonicalMetrics, consistency, extractions } = results;
  const allClaims = extractions.flatMap((e) => e.claims);
  const rows = [];

  for (const [area, names] of Object.entries(AREA_METRIC_MAP)) {
    const relatedDiscrepancies = consistency.discrepancies.filter((d) => names.includes(d.canonical_name));
    const hasMetric = canonicalMetrics.some((m) => names.includes(m.canonical_name));
    if (!hasMetric) continue;
    const exposure = relatedDiscrepancies.length
      ? Math.min(100, Math.round(Math.max(...relatedDiscrepancies.map((d) => d.max_delta_percent)) * 1.4))
      : 20;
    rows.push({ area, exposure });
  }

  rows.push({
    area: "Claims",
    exposure: allClaims.length ? Math.round((consistency.unsupported_claims.length / allClaims.length) * 100) : 0,
  });

  for (const [area, category] of Object.entries(AREA_CLAIM_CATEGORY_MAP)) {
    const inCategory = allClaims.filter((c) => c.category === category);
    if (inCategory.length === 0) continue;
    const unsupportedInCategory = inCategory.filter((c) => !c.has_supporting_data).length;
    rows.push({ area, exposure: Math.round((unsupportedInCategory / inCategory.length) * 100) });
  }

  return rows.map((r) => ({
    ...r,
    tier: r.exposure >= 70 ? "high" : r.exposure >= 40 ? "medium" : "low",
  }));
}

function computeContradictionMatrix(results) {
  const { canonicalMetrics, consistency } = results;
  const filenames = [...new Set(canonicalMetrics.map((m) => m.source.filename))];
  const discrepancyNames = new Set(consistency.discrepancies.map((d) => d.canonical_name));

  const candidateNames = [...new Set(
    canonicalMetrics.filter((m) => m.name_match_confidence >= 0.85).map((m) => m.canonical_name)
  )];
  const ordered = [
    ...candidateNames.filter((n) => discrepancyNames.has(n)),
    ...candidateNames.filter((n) => !discrepancyNames.has(n)),
  ].slice(0, 7);

  return ordered.map((name) => {
    const discrepancy = consistency.discrepancies.find((d) => d.canonical_name === name);
    const flaggedFiles = new Set((discrepancy?.values || []).map((v) => v.filename));
    const cells = filenames.map((filename) => {
      const present = canonicalMetrics.some((m) => m.canonical_name === name && m.source.filename === filename);
      if (!present) return "na";
      if (discrepancy) return flaggedFiles.has(filename) ? "inconsistent" : "partial";
      return "consistent";
    });
    return { name, cells };
  }).filter((r) => r.cells.some((c) => c !== "na"));
}

const CELL_ICON = { consistent: "✓", inconsistent: "✕", partial: "△", na: "–" };
const CELL_CLASS = { consistent: "cell-ok", inconsistent: "cell-bad", partial: "cell-warn", na: "cell-na" };

export default function Dashboard({ results, onReset }) {
  const { companyName, extractions, canonicalMetrics, consistency, risk, summary } = results;

  const stats = computeStats(results);
  const heatmap = computeRiskHeatmap(results);
  const matrix = computeContradictionMatrix(results);
  const filenames = [...new Set(canonicalMetrics.map((m) => m.source.filename))];

  const chartMetrics = canonicalMetrics
    .filter((m) => m.name_match_confidence >= 0.85 && !m.is_percent)
    .slice(0, 8)
    .map((m) => ({ name: m.canonical_name, value: m.value }));

  const severityCounts = ["high", "medium", "low"]
    .map((sev) => ({ name: sev, value: risk.flags.filter((f) => f.severity === sev).length }))
    .filter((d) => d.value > 0);

  const handleDownload = async () => {
    const blob = await generateReport(companyName, extractions, canonicalMetrics, consistency, risk, summary);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${companyName.replace(/\s+/g, "_")}_report.pdf`; a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="dashboard">
      <div className="dash-header">
        <div>
          <p className="mono dash-label">CASE FILE</p>
          <h2>{companyName}</h2>
        </div>
        <div className="dash-actions">
          <button className="cta small" onClick={handleDownload}>Download Report</button>
          <button className="cta secondary small" onClick={onReset}>New Analysis</button>
        </div>
      </div>

      <p className="dash-summary">{summary}</p>

      <div className="stat-row">
        {stats.map((s) => (
          <div className={`stat-card ${s.warn ? "warn" : ""} ${s.danger ? "danger" : ""} ${s.good ? "good" : ""}`} key={s.label}>
            <p className="stat-value mono">{s.value}</p>
            <p className="stat-label">{s.label}</p>
            {s.sub && <p className="stat-sub mono">{s.sub}</p>}
          </div>
        ))}
      </div>

      <div className="dash-grid">
        <div className="dash-card wide">
          <h3>Key Metrics</h3>
          {chartMetrics.length === 0 ? (
            <p className="muted">No confidently-matched numeric metrics found.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartMetrics} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid stroke="#2A332E" horizontal={false} />
                <XAxis type="number" tick={AXIS_TICK} />
                <YAxis dataKey="name" type="category" width={130} tick={AXIS_TICK} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => v.toLocaleString()} />
                <Bar dataKey="value" fill="#E8834F" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="dash-card">
          <h3>Risk Flags by Severity</h3>
          {severityCounts.length === 0 ? (
            <p className="muted">No risk flags triggered.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={severityCounts} dataKey="value" nameKey="name" innerRadius={42} outerRadius={72}>
                  {severityCounts.map((d, i) => <Cell key={i} fill={SEVERITY_COLOR[d.name]} />)}
                </Pie>
                <Legend wrapperStyle={{ color: "#8A9690", fontSize: 12 }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <section className="dash-section">
        <h3>Risk Heatmap (by Area)</h3>
        <div className="heatmap">
          {heatmap.map((row) => (
            <div className="heat-row" key={row.area}>
              <div className="heat-label">
                <span>{row.area}</span>
                <span className={`heat-tier tier-${row.tier}`}>{row.tier}</span>
              </div>
              <div className="heat-bar-track">
                <div className={`heat-bar-fill tier-${row.tier}`} style={{ width: `${row.exposure}%` }} />
              </div>
              <span className="heat-pct mono">{row.exposure}%</span>
            </div>
          ))}
        </div>
      </section>

      <section className="dash-section">
        <h3>Contradiction Matrix</h3>
        {matrix.length === 0 ? (
          <p className="muted">Not enough overlapping metrics to compare.</p>
        ) : (
          <div className="matrix-scroll">
            <table className="matrix-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {filenames.map((f) => <th key={f} title={f}>{f.length > 14 ? f.slice(0, 12) + "…" : f}</th>)}
                </tr>
              </thead>
              <tbody>
                {matrix.map((row) => (
                  <tr key={row.name}>
                    <td className="matrix-metric">{row.name}</td>
                    {row.cells.map((c, i) => (
                      <td key={i} className={CELL_CLASS[c]}>{CELL_ICON[c]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="matrix-legend">
          <span className="cell-ok">✓</span> Consistent &nbsp;
          <span className="cell-bad">✕</span> Inconsistent &nbsp;
          <span className="cell-warn">△</span> Partial &nbsp;
          <span className="cell-na">–</span> Not Available
        </div>
      </section>

      <section className="dash-section">
        <h3>Top Unsupported Claims</h3>
        {consistency.unsupported_claims.length === 0 ? (
          <p className="muted">All claims were backed by supporting data.</p>
        ) : (
          <ol className="claims-list">
            {consistency.unsupported_claims.slice(0, 5).map((c, i) => (
              <li key={i}>
                <span className="claim-text">"{c.claim_text}"</span>
                <span className="claim-page mono">p.{c.page}</span>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="dash-section">
        <h3>Discrepancies</h3>
        {consistency.discrepancies.length === 0 ? (
          <p className="muted">None detected.</p>
        ) : consistency.discrepancies.map((d, i) => (
          <div className="stamp-row" key={i}>
            <StampBadge label={`${d.max_delta_percent}% delta`} tone={d.severity === "high" ? "flagged" : "amber"} tilt={i % 2 ? -3 : 3} />
            <div>
              <p className="stamp-title">{d.canonical_name}</p>
              <p className="stamp-detail mono">{d.period_key}</p>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}