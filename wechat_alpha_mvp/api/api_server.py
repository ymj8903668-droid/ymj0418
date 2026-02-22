"""FastAPI service for querying hot topics and speaker rankings."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query

from wechat_alpha_mvp.database.models import Database
from wechat_alpha_mvp.stats.person_ranker import PersonRanker

app = FastAPI(title="wechat_alpha_mvp")
db = Database()
ranker = PersonRanker(db)


@app.get("/hot_topics")
def hot_topics(minutes: int = Query(default=60, ge=10, le=1440), limit: int = Query(default=10, ge=1, le=100)):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes)

    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT topic_name, SUM(mention_count) AS total_mentions
            FROM topic_heat
            WHERE window_end > %s AND window_end <= %s
            GROUP BY topic_name
            ORDER BY total_mentions DESC
            LIMIT %s
            """,
            (start_time, end_time, limit),
        )
        return {"items": cur.fetchall(), "window_minutes": minutes}


@app.get("/top_speakers")
def top_speakers(limit: int = Query(default=10, ge=1, le=100)):
    return {
        "top_stock_speakers": ranker.top_stock_speakers(limit),
        "most_active_speakers": ranker.most_active_speakers(limit),
        "first_topic_mentions": ranker.first_topic_mentions(),
    }


@app.get("/recent_messages")
def recent_messages(limit: int = Query(default=50, ge=1, le=500)):
    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, sender, group_name, content, sent_at
            FROM messages
            ORDER BY sent_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return {"items": cur.fetchall()}
