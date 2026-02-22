"""Person ranking queries."""

from __future__ import annotations

from wechat_alpha_mvp.database.models import Database


class PersonRanker:
    def __init__(self, db: Database) -> None:
        self.db = db

    def top_stock_speakers(self, limit: int = 10) -> list[dict]:
        with self.db.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.sender, COUNT(*) AS stock_mentions
                FROM message_stock_map ms
                JOIN messages m ON m.id = ms.message_id
                GROUP BY m.sender
                ORDER BY stock_mentions DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    def most_active_speakers(self, limit: int = 10) -> list[dict]:
        with self.db.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender, COUNT(*) AS message_count
                FROM messages
                GROUP BY sender
                ORDER BY message_count DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    def first_topic_mentions(self) -> list[dict]:
        with self.db.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (mt.topic_name)
                    mt.topic_name,
                    m.sender,
                    m.sent_at
                FROM message_topic_map mt
                JOIN messages m ON m.id = mt.message_id
                ORDER BY mt.topic_name, m.sent_at ASC
                """
            )
            return cur.fetchall()
