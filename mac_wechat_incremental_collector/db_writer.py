"""Write normalized messages to SQLite or PostgreSQL."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any



@dataclass(slots=True)
class NormalizedMessage:
    msg_id: int
    sender: str
    group_name: str
    content: str
    create_time: datetime
    message_hash: str
    source_db: str
    source_type: str = "db_read"


class DBWriter:
    def __init__(self, db_type: str, sqlite_path: str, postgres_dsn: str) -> None:
        self.db_type = db_type
        self.sqlite_path = sqlite_path
        self.postgres_dsn = postgres_dsn
        self._init_schema()

    def _connect(self):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
        import psycopg

        return psycopg.connect(self.postgres_dsn)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            if self.db_type == "sqlite":
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        msg_id BIGINT NOT NULL,
                        sender TEXT NOT NULL,
                        group_name TEXT NOT NULL,
                        content TEXT NOT NULL,
                        create_time TEXT NOT NULL,
                        message_hash TEXT NOT NULL UNIQUE,
                        source_db TEXT NOT NULL,
                        source_type TEXT NOT NULL DEFAULT 'db_read',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(msg_id, source_db)
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS collector_state (
                        source_db TEXT PRIMARY KEY,
                        last_processed_id BIGINT NOT NULL,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            else:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id BIGSERIAL PRIMARY KEY,
                        msg_id BIGINT NOT NULL,
                        sender TEXT NOT NULL,
                        group_name TEXT NOT NULL,
                        content TEXT NOT NULL,
                        create_time TIMESTAMPTZ NOT NULL,
                        message_hash TEXT NOT NULL UNIQUE,
                        source_db TEXT NOT NULL,
                        source_type TEXT NOT NULL DEFAULT 'db_read',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE(msg_id, source_db)
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS collector_state (
                        source_db TEXT PRIMARY KEY,
                        last_processed_id BIGINT NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
            conn.commit()

    def get_last_processed_id(self, source_db: str) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT last_processed_id FROM collector_state WHERE source_db = %s" if self.db_type == "postgres" else "SELECT last_processed_id FROM collector_state WHERE source_db = ?", (source_db,))
            row = cur.fetchone()
            if not row:
                return 0
            if self.db_type == "sqlite":
                return int(row["last_processed_id"])
            return int(row[0])

    def update_last_processed_id(self, source_db: str, last_processed_id: int) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            if self.db_type == "sqlite":
                cur.execute(
                    """
                    INSERT INTO collector_state(source_db, last_processed_id, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(source_db) DO UPDATE SET
                      last_processed_id = excluded.last_processed_id,
                      updated_at = CURRENT_TIMESTAMP
                    """,
                    (source_db, last_processed_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO collector_state(source_db, last_processed_id, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT(source_db) DO UPDATE SET
                      last_processed_id = EXCLUDED.last_processed_id,
                      updated_at = NOW()
                    """,
                    (source_db, last_processed_id),
                )
            conn.commit()

    def message_hash_exists(self, message_hash: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM messages WHERE message_hash = %s LIMIT 1" if self.db_type == "postgres" else "SELECT 1 FROM messages WHERE message_hash = ? LIMIT 1", (message_hash,))
            return cur.fetchone() is not None

    def write_messages(self, messages: list[NormalizedMessage]) -> int:
        if not messages:
            return 0

        inserted = 0
        with self._connect() as conn:
            cur = conn.cursor()
            for msg in messages:
                if self.db_type == "sqlite":
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO messages
                        (msg_id, sender, group_name, content, create_time, message_hash, source_db, source_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            msg.msg_id,
                            msg.sender,
                            msg.group_name,
                            msg.content,
                            msg.create_time.isoformat(),
                            msg.message_hash,
                            msg.source_db,
                            msg.source_type,
                        ),
                    )
                    inserted += int(cur.rowcount > 0)
                else:
                    cur.execute(
                        """
                        INSERT INTO messages
                        (msg_id, sender, group_name, content, create_time, message_hash, source_db, source_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (message_hash) DO NOTHING
                        """,
                        (
                            msg.msg_id,
                            msg.sender,
                            msg.group_name,
                            msg.content,
                            msg.create_time,
                            msg.message_hash,
                            msg.source_db,
                            msg.source_type,
                        ),
                    )
                    inserted += int(cur.rowcount > 0)
            conn.commit()
        return inserted
