import { useNavigate } from "react-router-dom";
import StampBadge from "../components/StampBadge";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow mono">DUE-DILIGENCE, VERIFIED LINE BY LINE</p>
          <h1>Every claim in a<br/>pitch deck deserves<br/>a second reading.</h1>
          <p className="hero-sub">
            Upload a startup's documents. This system extracts every number and
            claim, checks them against each other, flags what doesn't add up —
            and shows you exactly where it found it.
          </p>
          <button className="cta" onClick={() => navigate("/chat")}>
            Start an Analysis →
          </button>
        </div>

        <div className="hero-artifact">
          <div className="case-card">
            <p className="case-label mono">EXHIBIT A — p.9</p>
            <p className="case-line">
              "Seeking <span className="highlight">$900,000</span> seed funding for
              AI development, hiring, infrastructure, and expansion."
            </p>
            <StampBadge label="Unverified" tone="flagged" tilt={-6} />
          </div>
          <div className="leader-line" />
          <div className="case-card offset">
            <p className="case-label mono">EXHIBIT A — p.1</p>
            <p className="case-line">
              "Seeking <span className="highlight">$750,000</span> seed funding for
              product development and expansion."
            </p>
            <StampBadge label="Discrepancy · 20%" tone="amber" tilt={3} />
          </div>
        </div>
      </section>

      <section className="how">
        <h2>How a document becomes evidence</h2>
        <div className="how-grid">
          {[
            ["Extract", "Every number and claim is pulled out with its exact source page — nothing is summarized before it's checked."],
            ["Reconcile", "The same metric, reported in two different documents, is compared. Disagreements are flagged, not smoothed over."],
            ["Rule-check", "Named, evidence-linked rules catch burn rate, runway, and unsupported-claim patterns — no black-box scoring."],
            ["Answer & Report", "Ask questions in chat or export a full report — every answer traces back to the original sentence."],
          ].map(([title, body], i) => (
            <div className="how-card" key={title}>
              <p className="how-index mono">0{i + 1}</p>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="closing">
        <h2>No verdicts. Just evidence.</h2>
        <p>
          This tool doesn't tell you whether to invest. It tells you what's
          consistent, what isn't, and what's asserted without support —
          with a citation for every claim.
        </p>
        <button className="cta secondary" onClick={() => navigate("/chat")}>
          Upload your first document
        </button>
      </section>
    </div>
  );
}