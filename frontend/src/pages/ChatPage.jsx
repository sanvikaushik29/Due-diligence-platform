import { useState, useRef } from "react";
import {
  extractDocument, canonicalizeDocument, consistencyCheck,
  riskAssessment, openingSummary, indexSession, saveSession,
} from "../api";
import ChatPanel from "../components/ChatPanel";
import Dashboard from "../components/Dashboard";
import { useSession } from "../context/SessionContext";
import "./ChatPage.css";

export default function ChatPage() {
  const { results, setResults, reset: resetSession } = useSession();
  const [stage, setStage] = useState(results ? "ready" : "landing");
  const [companyName, setCompanyName] = useState("");
  const [files, setFiles] = useState([]);
  const [log, setLog] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const fileInputRef = useRef(null);

  const addLog = (msg) => setLog((prev) => [...prev, msg]);

  const runPipeline = async () => {
    if (files.length === 0 || !companyName.trim()) return;
    setStage("processing");
    setLog([]);
    setErrorMsg("");

    try {
      const extractions = [];
      const canonicalMetrics = [];

      for (const file of files) {
        addLog(`Extracting ${file.name}...`);
        const extraction = await extractDocument(file);
        extractions.push(extraction);

        addLog(`Canonicalizing metrics from ${file.name}...`);
        const canon = await canonicalizeDocument(extraction);
        canonicalMetrics.push(...canon);
      }

      addLog("Checking cross-document consistency...");
      const consistency = await consistencyCheck(canonicalMetrics, extractions);

      addLog("Running risk assessment...");
      const risk = await riskAssessment(canonicalMetrics, extractions);

      addLog("Generating summary...");
      const summary = await openingSummary(risk, consistency);

      addLog("Indexing for chat...");
      const sessionId = crypto.randomUUID();
      await indexSession(sessionId, extractions, canonicalMetrics, consistency, risk);

      addLog("Saving session...");
      await saveSession(sessionId, companyName, extractions, canonicalMetrics, consistency, risk, summary);

      setResults({ extractions, canonicalMetrics, consistency, risk, summary, sessionId, companyName });
      setStage("ready");
    } catch (err) {
      console.error(err);
      setErrorMsg(err?.response?.data?.detail || err.message || "Something went wrong.");
      setStage("error");
    }
  };

  const reset = () => {
    resetSession();
    setStage("landing"); setFiles([]); setCompanyName("");
    setLog([]); setErrorMsg("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  if (results) {
    return (
      <div className="split-screen">
        <div className="split-left"><Dashboard results={results} onReset={reset} /></div>
        <div className="split-right"><ChatPanel sessionId={results.sessionId} openingSummary={results.summary} /></div>
      </div>
    );
  }

  return (
    <div className="chat-intro">
      <div className="intro-left">
        <p className="eyebrow mono">ASK ANYTHING, CITED EVERY TIME</p>
        <div className="mock-chat">
          <div className="mock-bubble assistant">
            I've reviewed 2 documents. The funding ask differs by 20% between
            them, and 72% of claims have no supporting data. Ask me anything.
          </div>
          <div className="mock-bubble user">What's the discrepancy in the funding ask?</div>
          <div className="mock-bubble assistant">
            $750,000 (p.1) vs $900,000 (p.9) — a 20% difference.
            <div className="mock-citations">
              <span className="mono chip">deck.pdf · p.1</span>
              <span className="mono chip">deck.pdf · p.9</span>
            </div>
          </div>
        </div>
      </div>

      <div className="intro-right">
        <div className="upload-card">
          {stage === "error" && <div className="error-banner">⚠ {errorMsg}</div>}

          {stage === "processing" ? (
            <div className="processing-block">
              <div className="spinner" />
              <ul className="progress-log mono">
                {log.map((line, i) => <li key={i}>{line}</li>)}
              </ul>
            </div>
          ) : (
            <>
              <h2>Start an analysis</h2>
              <label className="field-label">Company name</label>
              <input className="text-input" placeholder="e.g. EcoCart" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />

              <label className="field-label">Documents (PDF)</label>
              <input ref={fileInputRef} type="file" accept=".pdf" multiple onChange={(e) => setFiles(Array.from(e.target.files))} className="file-input" />
              {files.length > 0 && (
                <ul className="file-list mono">{files.map((f) => <li key={f.name}>{f.name}</li>)}</ul>
              )}

              <button className="cta full-width" disabled={files.length === 0 || !companyName.trim()} onClick={runPipeline}>
                Analyze Documents
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}