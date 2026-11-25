import { useState, useRef, useEffect } from "react";
import { chatQuery } from "../api";
import "./ChatPanel.css";

function dedupeCitations(citations) {
  const seen = new Set();
  return citations.filter((c) => {
    const key = `${c.filename}-${c.page}-${c.raw_text}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ChatPanel({ sessionId, openingSummary }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: openingSummary, citations: [], time: timeNow() },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input, time: timeNow() };
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await chatQuery(sessionId, userMsg.content, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, citations: res.citations, time: timeNow() }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Something went wrong answering that.", citations: [], time: timeNow() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="console">
      <div className="console-header">
        <div className="console-avatar">◆</div>
        <div>
          <p className="console-title">Analyst</p>
          <p className="console-status"><span className="dot" /> grounded in uploaded documents</p>
        </div>
      </div>

      <div className="console-messages">
        {messages.map((m, i) => (
          <div className={`msg-row ${m.role}`} key={i}>
            {m.role === "assistant" && <div className="avatar assistant-avatar">◆</div>}
            <div className="msg-col">
              <div className={`bubble ${m.role}`}>
                <p>{m.content}</p>
              </div>
              {m.citations && m.citations.length > 0 && (
                <div className="citations">
                  {dedupeCitations(m.citations).map((c, j) => (
                    <div key={j} className="citation-chip mono">{c.filename} · p.{c.page}</div>
                  ))}
                </div>
              )}
              <span className="msg-time mono">{m.time}</span>
            </div>
            {m.role === "user" && <div className="avatar user-avatar">Y</div>}
          </div>
        ))}

        {loading && (
          <div className="msg-row assistant">
            <div className="avatar assistant-avatar">◆</div>
            <div className="bubble assistant typing-bubble">
              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="console-input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the documents..."
          rows={1}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>➤</button>
      </div>
    </div>
  );
}