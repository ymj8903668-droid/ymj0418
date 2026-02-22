"""Topic heat aggregation job."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from wechat_alpha_mvp.database.models import Database


class TopicHeatCalculator:
    def __init__(self, db: Database) -> None:
        self.db = db

    def run(self, window_minutes: int = 10) -> int:
        window_end = datetime.now(timezone.utc)
        minute = (window_end.minute // window_minutes) * window_minutes
        window_end = window_end.replace(minute=minute, second=0, microsecond=0)
        window_start = window_end - timedelta(minutes=window_minutes)

        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT mt.topic_name, COUNT(*) AS mention_count
                    FROM message_topic_map mt
                    JOIN messages m ON m.id = mt.message_id
                    WHERE m.sent_at >= %s AND m.sent_at < %s
                    GROUP BY mt.topic_name
                    """,
                    (window_start, window_end),
                )
                rows = cur.fetchall()

                for row in rows:
                    cur.execute(
                        """
                        INSERT INTO topic_heat(window_start, window_end, topic_name, mention_count)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (window_start, window_end, topic_name)
                        DO UPDATE SET mention_count = EXCLUDED.mention_count
                        """,
                        (window_start, window_end, row["topic_name"], row["mention_count"]),
                    )
                return len(rows)
