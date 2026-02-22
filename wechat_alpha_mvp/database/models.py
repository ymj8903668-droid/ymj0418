"""Database helpers and SQL access layer."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


@dataclass(slots=True)
class MessageRecord:
    id: int
    raw_id: int
    sender: str
    group_name: str
    content: str
    sent_at: datetime


class Database:
    """Thin wrapper around psycopg connection management."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/wechat_alpha",
        )

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection]:
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
