import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listSessions, getSession } from "../api";
import { useSession } from "../context/SessionContext";
import "./HistoryPage.css";

export default function HistoryPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const { setResults } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    listSessions().then((data) => { setSessions(data); setLoading(false); });
  }, []);

  const loadSession = async (sessionId) => {
    const full = await getSession(sessionId);
    setResults({
      extractions: full.extractions,
      canonicalMetrics: full.canonical_metrics,
      consistency: full.consistency,
      risk: full.risk,
      summary: full.summary,
      sessionId: full.session_id,
      companyName: full.company_name,
    });
    navigate("/chat");
  };

  return (
    <div className="history-page">
      <p className="mono eyebrow">PAST ANALYSES</p>
      <h2>History</h2>
      {loading && <p className="muted">Loading...</p>}
      {!loading && sessions.length === 0 && <p className="muted">No saved sessions yet.</p>}
      <div className="history-list">
        {sessions.map((s) => (
          <button className="history-card" key={s.session_id} onClick={() => loadSession(s.session_id)}>
            <span className="history-name">{s.company_name}</span>
            <span className="history-date mono">{new Date(s.created_at).toLocaleString()}</span>
          </button>
        ))}
      </div>
    </div>
  );
}