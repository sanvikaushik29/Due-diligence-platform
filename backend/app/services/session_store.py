import json
from datetime import datetime
from app.db import get_conn

def save_session(session_id, company_name, extractions, canonical_metrics, consistency, risk, summary):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO sessions (session_id, company_name, created_at, extractions, canonical_metrics, consistency, risk, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                company_name=excluded.company_name,
                extractions=excluded.extractions,
                canonical_metrics=excluded.canonical_metrics,
                consistency=excluded.consistency,
                risk=excluded.risk,
                summary=excluded.summary
        """, (
            session_id, company_name, datetime.utcnow().isoformat(),
            json.dumps(extractions), json.dumps(canonical_metrics),
            json.dumps(consistency), json.dumps(risk), summary
        ))
        conn.commit()

def list_sessions():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT session_id, company_name, created_at FROM sessions ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

def get_session(session_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["extractions"] = json.loads(d["extractions"])
        d["canonical_metrics"] = json.loads(d["canonical_metrics"])
        d["consistency"] = json.loads(d["consistency"])
        d["risk"] = json.loads(d["risk"])
        return d

def delete_session(session_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()