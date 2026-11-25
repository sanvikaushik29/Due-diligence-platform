import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app_data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            extractions TEXT NOT NULL,
            canonical_metrics TEXT NOT NULL,
            consistency TEXT NOT NULL,
            risk TEXT NOT NULL,
            summary TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()