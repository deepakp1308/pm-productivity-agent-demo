"""SQLite storage with FTS5 for the PM Productivity Agent."""

import json
import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_db_path: Optional[str] = None


def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        _db_path = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "pm_agent.db"))
    return os.path.abspath(_db_path)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables and FTS5 index if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS team_members (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'pm',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS priorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                weight REAL DEFAULT 1.0,
                active INTEGER DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pm_id TEXT NOT NULL REFERENCES team_members(id),
                source TEXT NOT NULL,
                source_id TEXT,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                duration_minutes INTEGER,
                participants TEXT DEFAULT '[]',
                url TEXT DEFAULT '',
                occurred_at TEXT NOT NULL,
                ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, source_id)
            );

            CREATE TABLE IF NOT EXISTS activity_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL REFERENCES activities(id),
                priority_id INTEGER REFERENCES priorities(id),
                priority_name TEXT,
                activity_type TEXT,
                leverage TEXT,
                confidence REAL,
                reasoning TEXT DEFAULT '',
                classified_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_iso TEXT NOT NULL,
                pm_id TEXT REFERENCES team_members(id),
                pm_name TEXT,
                kind TEXT NOT NULL,
                action TEXT NOT NULL,
                rationale TEXT NOT NULL,
                evidence_ids TEXT DEFAULT '[]',
                judge_score REAL,
                judge_reasoning TEXT,
                status TEXT DEFAULT 'published',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_iso TEXT NOT NULL,
                triggered_by TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                activities_ingested INTEGER DEFAULT 0,
                activities_classified INTEGER DEFAULT 0,
                recommendations_generated INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                context_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_activities_pm ON activities(pm_id);
            CREATE INDEX IF NOT EXISTS idx_activities_source ON activities(source);
            CREATE INDEX IF NOT EXISTS idx_activities_occurred ON activities(occurred_at DESC);
            CREATE INDEX IF NOT EXISTS idx_classifications_activity ON activity_classifications(activity_id);
            CREATE INDEX IF NOT EXISTS idx_recommendations_week ON recommendations(week_iso);
            CREATE INDEX IF NOT EXISTS idx_recommendations_pm ON recommendations(pm_id);
        """)
        # FTS5 virtual table for full-text search on activities
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS activities_fts
            USING fts5(title, summary, source, content=activities, content_rowid=id)
        """)
        conn.commit()
        logger.info(f"Database initialized at {_get_db_path()}")
    finally:
        conn.close()


def reset_db():
    """Drop all tables and reinitialize."""
    path = _get_db_path()
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Removed existing database at {path}")
    init_db()


# ── Team members ───────────────────────────────────────────────────────────────

def upsert_team_member(id: str, name: str, email: str, role: str = "pm"):
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO team_members (id, name, email, role) VALUES (?, ?, ?, ?)",
            (id, name, email, role),
        )
        conn.commit()
    finally:
        conn.close()


def get_team_members() -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT * FROM team_members ORDER BY name").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_team_member(pm_id: str) -> Optional[dict]:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM team_members WHERE id = ?", (pm_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Priorities ─────────────────────────────────────────────────────────────────

def insert_priority(name: str, description: str = "", weight: float = 1.0) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO priorities (name, description, weight) VALUES (?, ?, ?)",
            (name, description, weight),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_priorities(active_only: bool = True) -> list[dict]:
    conn = _get_conn()
    try:
        q = "SELECT * FROM priorities"
        if active_only:
            q += " WHERE active = 1"
        q += " ORDER BY id"
        rows = conn.execute(q).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_priority(id: int, **kwargs):
    conn = _get_conn()
    try:
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("name", "description", "weight", "active"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        sets.append("updated_at = datetime('now')")
        vals.append(id)
        conn.execute(f"UPDATE priorities SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


def delete_priority(id: int):
    conn = _get_conn()
    try:
        conn.execute("UPDATE priorities SET active = 0, updated_at = datetime('now') WHERE id = ?", (id,))
        conn.commit()
    finally:
        conn.close()


# ── Activities ─────────────────────────────────────────────────────────────────

def insert_activity(pm_id: str, source: str, title: str, occurred_at: str,
                    source_id: str = None, summary: str = "", duration_minutes: int = None,
                    participants: list[str] = None, url: str = "") -> Optional[int]:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT OR IGNORE INTO activities
               (pm_id, source, source_id, title, summary, duration_minutes, participants, url, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pm_id, source, source_id, title, summary, duration_minutes,
             json.dumps(participants or []), url, occurred_at),
        )
        conn.commit()
        if cur.lastrowid:
            # Keep FTS5 in sync
            conn.execute(
                "INSERT INTO activities_fts(rowid, title, summary, source) VALUES (?, ?, ?, ?)",
                (cur.lastrowid, title, summary, source),
            )
            conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_activities_bulk(rows: list[dict]) -> int:
    """Bulk insert activities. Returns count inserted."""
    conn = _get_conn()
    count = 0
    try:
        for r in rows:
            cur = conn.execute(
                """INSERT OR IGNORE INTO activities
                   (pm_id, source, source_id, title, summary, duration_minutes, participants, url, occurred_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["pm_id"], r["source"], r.get("source_id"), r["title"],
                 r.get("summary", ""), r.get("duration_minutes"),
                 json.dumps(r.get("participants", [])), r.get("url", ""), r["occurred_at"]),
            )
            if cur.lastrowid:
                conn.execute(
                    "INSERT INTO activities_fts(rowid, title, summary, source) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, r["title"], r.get("summary", ""), r["source"]),
                )
                count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def get_activities(pm_id: str = None, source: str = None, priority_name: str = None,
                   date_from: str = None, date_to: str = None,
                   limit: int = 200, offset: int = 0) -> list[dict]:
    conn = _get_conn()
    try:
        q = """SELECT a.*, ac.priority_name, ac.activity_type, ac.leverage, ac.confidence, ac.reasoning
               FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id"""
        wheres = []
        params = []
        if pm_id:
            wheres.append("a.pm_id = ?")
            params.append(pm_id)
        if source:
            wheres.append("a.source = ?")
            params.append(source)
        if priority_name:
            wheres.append("ac.priority_name = ?")
            params.append(priority_name)
        if date_from:
            wheres.append("a.occurred_at >= ?")
            params.append(date_from)
        if date_to:
            wheres.append("a.occurred_at <= ?")
            params.append(date_to)
        if wheres:
            q += " WHERE " + " AND ".join(wheres)
        q += " ORDER BY a.occurred_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_activity(activity_id: int) -> Optional[dict]:
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT a.*, ac.priority_name, ac.activity_type, ac.leverage, ac.confidence, ac.reasoning
               FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE a.id = ?""",
            (activity_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_activity_count(pm_id: str = None) -> int:
    conn = _get_conn()
    try:
        q = "SELECT COUNT(*) as cnt FROM activities"
        params = []
        if pm_id:
            q += " WHERE pm_id = ?"
            params.append(pm_id)
        return conn.execute(q, params).fetchone()["cnt"]
    finally:
        conn.close()


def search_activities_fts(query: str, limit: int = 50) -> list[dict]:
    """Full-text search using FTS5."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT a.*, ac.priority_name, ac.activity_type, ac.leverage, ac.confidence
               FROM activities_fts fts
               JOIN activities a ON a.id = fts.rowid
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE activities_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Classifications ────────────────────────────────────────────────────────────

def insert_classification(activity_id: int, priority_id: int = None, priority_name: str = None,
                          activity_type: str = None, leverage: str = None,
                          confidence: float = None, reasoning: str = "") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO activity_classifications
               (activity_id, priority_id, priority_name, activity_type, leverage, confidence, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (activity_id, priority_id, priority_name, activity_type, leverage, confidence, reasoning),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_classifications_bulk(rows: list[dict]) -> int:
    conn = _get_conn()
    count = 0
    try:
        for r in rows:
            conn.execute(
                """INSERT INTO activity_classifications
                   (activity_id, priority_id, priority_name, activity_type, leverage, confidence, reasoning)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (r["activity_id"], r.get("priority_id"), r.get("priority_name"),
                 r.get("activity_type"), r.get("leverage"), r.get("confidence"), r.get("reasoning", "")),
            )
            count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def get_unclassified_activities(limit: int = 500) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT a.* FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE ac.id IS NULL
               ORDER BY a.occurred_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Recommendations ────────────────────────────────────────────────────────────

def insert_recommendation(week_iso: str, pm_id: str, pm_name: str, kind: str,
                          action: str, rationale: str, evidence_ids: list[int],
                          judge_score: float = None, judge_reasoning: str = None,
                          status: str = "published") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO recommendations
               (week_iso, pm_id, pm_name, kind, action, rationale, evidence_ids,
                judge_score, judge_reasoning, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (week_iso, pm_id, pm_name, kind, action, rationale,
             json.dumps(evidence_ids), judge_score, judge_reasoning, status),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_recommendations(week_iso: str = None, pm_id: str = None,
                        status: str = None, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        q = "SELECT * FROM recommendations"
        wheres = []
        params = []
        if week_iso:
            wheres.append("week_iso = ?")
            params.append(week_iso)
        if pm_id:
            wheres.append("pm_id = ?")
            params.append(pm_id)
        if status:
            wheres.append("status = ?")
            params.append(status)
        if wheres:
            q += " WHERE " + " AND ".join(wheres)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("evidence_ids"):
                d["evidence_ids"] = json.loads(d["evidence_ids"])
            else:
                d["evidence_ids"] = []
            result.append(d)
        return result
    finally:
        conn.close()


def get_latest_week_iso() -> Optional[str]:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT DISTINCT week_iso FROM recommendations ORDER BY week_iso DESC LIMIT 1"
        ).fetchone()
        return row["week_iso"] if row else None
    finally:
        conn.close()


# ── Pipeline runs ──────────────────────────────────────────────────────────────

def start_pipeline_run(week_iso: str, triggered_by: str) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO pipeline_runs (week_iso, triggered_by) VALUES (?, ?)",
            (week_iso, triggered_by),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_pipeline_run(run_id: int, **kwargs):
    conn = _get_conn()
    try:
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("status", "activities_ingested", "activities_classified",
                      "recommendations_generated", "error_message", "completed_at"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        vals.append(run_id)
        conn.execute(f"UPDATE pipeline_runs SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


def get_last_pipeline_run() -> Optional[dict]:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Chat ───────────────────────────────────────────────────────────────────────

def save_chat_message(session_id: str, role: str, content: str, context_json: str = None):
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, context_json) VALUES (?, ?, ?, ?)",
            (session_id, role, content, context_json),
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(session_id: str, limit: int = 20) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY created_at LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Generic SQL (for chat Q&A tool_use) ────────────────────────────────────────

def run_read_only_sql(query: str, params: list = None) -> list[dict]:
    """Execute a read-only SQL query. Used by the chat agent's tool_use."""
    q = query.strip().upper()
    if not q.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    conn = _get_conn()
    try:
        rows = conn.execute(query, params or []).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
