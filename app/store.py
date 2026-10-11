"""SQLite persistence: session snapshots + append-only long-format event log."""
import json
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (code TEXT PRIMARY KEY, state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_code TEXT NOT NULL, ts_utc TEXT NOT NULL,
  round INTEGER, participant_id TEXT, role TEXT, event_type TEXT NOT NULL,
  subject TEXT, field TEXT, before TEXT, after TEXT, detail TEXT
);
CREATE INDEX IF NOT EXISTS ix_events_session ON events(session_code, id);
"""
EVENT_COLS = ["session_code", "seq", "ts_utc", "round", "participant_id", "role", "event_type", "subject", "field", "before", "after", "detail"]


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.db.executescript(SCHEMA)

    def save_session(self, code: str, state: dict):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO sessions VALUES (?,?)", (code, json.dumps(state)))
            self.db.commit()

    def load_sessions(self) -> dict:
        with self.lock:
            return {c: json.loads(s) for c, s in self.db.execute("SELECT code, state FROM sessions")}

    def add_event(self, code, ts, rnd, pid, role, etype, subject=None, field=None, before=None, after=None, detail=None):
        with self.lock:
            self.db.execute(
                "INSERT INTO events (session_code, ts_utc, round, participant_id, role, event_type, subject, field, before, after, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (code, ts, rnd, pid, role, etype, subject, field,
                 None if before is None else str(before), None if after is None else str(after),
                 None if detail is None else json.dumps(detail, sort_keys=True)))
            self.db.commit()

    def events(self, code: str, etype: str = None):
        q = "SELECT session_code, id, ts_utc, round, participant_id, role, event_type, subject, field, before, after, detail FROM events WHERE session_code=?"
        args = [code]
        if etype:
            q += " AND event_type=?"
            args.append(etype)
        with self.lock:
            return self.db.execute(q + " ORDER BY id", args).fetchall()
