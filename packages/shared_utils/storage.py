"""SQLite-backed session storage for troubleshooting workflows."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from packages.schemas import TroubleshootingSession

from .logger import get_logger


class SessionStore:
    """Persist and retrieve session objects from SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = get_logger("systemdoctor.storage")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, session: TroubleshootingSession) -> None:
        session.touch()
        payload = json.dumps(session.to_storage_dict(), ensure_ascii=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions(session_id, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (
                    session.session_id,
                    payload,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                ),
            )
            conn.commit()
        self._logger.info("saved session_id=%s", session.session_id)

    def get(self, session_id: str) -> Optional[TroubleshootingSession]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

        if not row:
            return None

        payload = json.loads(row[0])
        return TroubleshootingSession.from_storage_dict(payload)

    def list_recent(self, limit: int = 20) -> List[TroubleshootingSession]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()

        sessions: List[TroubleshootingSession] = []
        for row in rows:
            sessions.append(TroubleshootingSession.from_storage_dict(json.loads(row[0])))
        return sessions
