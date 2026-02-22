"""Read incremental messages from a WeChat-sync table and parse into normalized tables."""

from __future__ import annotations

import logging
from typing import Any

from wechat_alpha_mvp.database.models import Database
from wechat_alpha_mvp.parser.message_parser import parse_raw_message
from wechat_alpha_mvp.parser.stock_matcher import StockMatcher
from wechat_alpha_mvp.parser.topic_matcher import TopicMatcher

logger = logging.getLogger(__name__)


class WeChatDBReader:
    def __init__(self, db: Database, stock_matcher: StockMatcher, topic_matcher: TopicMatcher) -> None:
        self.db = db
        self.stock_matcher = stock_matcher
        self.topic_matcher = topic_matcher

    def ingest_new_messages(self, batch_size: int = 1000) -> int:
        """Ingest only new records since last sync point."""
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT last_raw_id FROM sync_state WHERE id = 1")
                last_raw_id = cur.fetchone()["last_raw_id"]

                cur.execute(
                    """
                    SELECT id, sender, group_name, content, sent_at
                    FROM raw_wechat_messages
                    WHERE id > %s
                    ORDER BY id ASC
                    LIMIT %s
                    """,
                    (last_raw_id, batch_size),
                )
                rows = cur.fetchall()

                if not rows:
                    logger.info("No new messages found.")
                    return 0

                processed = 0
                max_raw_id = last_raw_id

                for row in rows:
                    parsed = parse_raw_message(row)
                    message_id = self._upsert_message(cur, parsed)
                    self._save_stock_matches(cur, message_id, parsed["content"])
                    self._save_topic_matches(cur, message_id, parsed["content"])

                    max_raw_id = max(max_raw_id, row["id"])
                    processed += 1

                cur.execute(
                    """
                    UPDATE sync_state
                    SET last_raw_id = %s, updated_at = NOW()
                    WHERE id = 1
                    """,
                    (max_raw_id,),
                )
                logger.info("Ingested %s new message(s).", processed)
                return processed

    def _upsert_message(self, cur: Any, parsed: dict[str, Any]) -> int:
        cur.execute(
            """
            INSERT INTO messages(raw_id, sender, group_name, content, sent_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (raw_id) DO UPDATE
            SET sender = EXCLUDED.sender,
                group_name = EXCLUDED.group_name,
                content = EXCLUDED.content,
                sent_at = EXCLUDED.sent_at
            RETURNING id
            """,
            (
                parsed["raw_id"],
                parsed["sender"],
                parsed["group_name"],
                parsed["content"],
                parsed["sent_at"],
            ),
        )
        return cur.fetchone()["id"]

    def _save_stock_matches(self, cur: Any, message_id: int, content: str) -> None:
        for match in self.stock_matcher.match(content):
            cur.execute(
                """
                INSERT INTO message_stock_map(message_id, stock_code, stock_name, matched_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (message_id, stock_code) DO NOTHING
                """,
                (message_id, match["stock_code"], match["stock_name"], match["matched_text"]),
            )

    def _save_topic_matches(self, cur: Any, message_id: int, content: str) -> None:
        for match in self.topic_matcher.match(content):
            cur.execute(
                """
                INSERT INTO message_topic_map(message_id, topic_name, matched_keyword)
                VALUES (%s, %s, %s)
                ON CONFLICT (message_id, topic_name) DO NOTHING
                """,
                (message_id, match["topic_name"], match["matched_keyword"]),
            )
