"""Long-running scheduler for ingestion and aggregation."""

from __future__ import annotations

import logging
import time

from wechat_alpha_mvp.database.models import Database
from wechat_alpha_mvp.ingestion.wechat_db_reader import WeChatDBReader
from wechat_alpha_mvp.parser.stock_matcher import StockMatcher
from wechat_alpha_mvp.parser.topic_matcher import TopicMatcher
from wechat_alpha_mvp.stats.topic_heat_calculator import TopicHeatCalculator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_forever() -> None:
    db = Database()
    stock_matcher = StockMatcher()
    topic_matcher = TopicMatcher()
    reader = WeChatDBReader(db, stock_matcher, topic_matcher)
    heat_calculator = TopicHeatCalculator(db)

    loop_count = 0
    while True:
        try:
            reader.ingest_new_messages()

            # Every 10 rounds (1 min x 10 = 10 mins), refresh topic heat.
            if loop_count % 10 == 0:
                count = heat_calculator.run(window_minutes=10)
                logger.info("Topic heat updated for %s topics.", count)

            loop_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("Scheduler loop failed: %s", exc)

        time.sleep(60)


if __name__ == "__main__":
    run_forever()
