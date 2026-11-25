export default function FindingsPanel({ results, onDownloadReport, onReset }) {
  const { consistency, risk } = results;
  const discrepancies = consistency.discrepancies || [];
  const flags = risk.flags || [];

  return (
    <div className="findings-panel">
      <div className="findings-header">
        <h2>Findings</h2>
        <button className="secondary-btn small" onClick={onReset}>New Analysis</button>
      </div>

      <button className="primary-btn full-width" onClick={onDownloadReport}>
        Download Full Report (PDF)
      </button>

      <section>
        <h3>Discrepancies ({discrepancies.length})</h3>
        {discrepancies.length === 0 && <p className="muted">None detected.</p>}
        {discrepancies.map((d, i) => (
          <div key={i} className={`finding-card severity-${d.severity}`}>
            <div className="finding-title">{d.canonical_name}</div>
            <div className="finding-detail">{d.max_delta_percent}% delta · {d.period_key}</div>
          </div>
        ))}
      </section>

      <section>
        <h3>Risk Flags ({flags.length})</h3>
        {flags.length === 0 && <p className="muted">No rules triggered.</p>}
        {flags.map((f, i) => (
          <div key={i} className={`finding-card severity-${f.severity}`}>
            <div className="finding-title">{f.rule_name}</div>
            <div className="finding-detail">{f.description}</div>
          </div>
        ))}
      </section>
    </div>
  );
}