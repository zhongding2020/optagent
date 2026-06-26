import json
import sqlite3
from pathlib import Path
from typing import Optional
from ..models.session import SessionMetadata, SessionCreate, NodeStatus


class SessionStore:
    def __init__(self, db_path: str = "./data/sessions.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    workflow_name TEXT NOT NULL,
                    workflow_version TEXT NOT NULL DEFAULT '1.0',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checkpoint_id TEXT,
                    current_node TEXT,
                    node_statuses TEXT DEFAULT '{}',
                    node_results TEXT DEFAULT '{}'
                )
            """)
        # Migration: add column for existing databases
        try:
            with self._get_conn() as conn:
                conn.execute("ALTER TABLE sessions ADD COLUMN node_results TEXT DEFAULT '{}'")
        except sqlite3.OperationalError:
            pass

    def create(self, session: SessionCreate) -> SessionMetadata:
        import uuid
        meta = SessionMetadata(
            id=str(uuid.uuid4()),
            workflow_name=session.workflow_name,
        )
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, workflow_name, status) VALUES (?, ?, ?)",
                (meta.id, meta.workflow_name, meta.status),
            )
        return meta

    def get(self, session_id: str) -> Optional[SessionMetadata]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not row:
                return None
            try:
                raw = row["node_results"]
            except (IndexError, KeyError):
                raw = "{}"
            return SessionMetadata(
                id=row["id"],
                workflow_name=row["workflow_name"],
                workflow_version=row["workflow_version"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                checkpoint_id=row["checkpoint_id"],
                current_node=row["current_node"],
                node_statuses={
                    k: NodeStatus(**v)
                    for k, v in json.loads(row["node_statuses"]).items()
                },
                node_results=json.loads(raw) if raw else {},
            )

    def list(self) -> list[SessionMetadata]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC"
            ).fetchall()
            return [
                SessionMetadata(
                    id=r["id"], workflow_name=r["workflow_name"],
                    workflow_version=r["workflow_version"],
                    status=r["status"], created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    checkpoint_id=r["checkpoint_id"],
                    current_node=r["current_node"],
                    node_statuses={
                        k: NodeStatus(**v)
                        for k, v in json.loads(r["node_statuses"]).items()
                    },
                    node_results={},
                )
                for r in rows
            ]

    def update(self, meta: SessionMetadata):
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE sessions SET status=?, updated_at=?, checkpoint_id=?, current_node=?, node_statuses=?, node_results=?
                   WHERE id=?""",
                (meta.status, meta.updated_at.isoformat(),
                 meta.checkpoint_id, meta.current_node,
                 json.dumps({k: v.model_dump() for k, v in meta.node_statuses.items()}),
                 json.dumps(meta.node_results),
                 meta.id),
            )

    def delete(self, session_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
