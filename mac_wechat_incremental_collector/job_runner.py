"""Scheduler entrypoint for long-running incremental collection."""

from __future__ import annotations

import time
from pathlib import Path

from mac_wechat_incremental_collector.config import CollectorConfig
from mac_wechat_incremental_collector.db_reader import WeChatDBReader
from mac_wechat_incremental_collector.db_writer import DBWriter
from mac_wechat_incremental_collector.logger import setup_logger
from mac_wechat_incremental_collector.message_deduper import MessageDeduper


def run_once(config: CollectorConfig | None = None) -> dict[str, int]:
    config = config or CollectorConfig()
    config.validate()

    logger = setup_logger("mac_wechat_incremental_collector", config.log_file, config.log_level)
    writer = DBWriter(config.target_db_type, str(config.target_sqlite_path), config.target_postgres_dsn)
    deduper = MessageDeduper(writer)
    reader = WeChatDBReader(config)

    scanned_db_count = 0
    total_read = 0
    total_inserted = 0

    db_paths = reader.scan_source_dbs()
    if not db_paths:
        logger.warning("No source DB files found under %s with glob '%s'", config.wechat_db_dir, config.source_db_glob)

    for source_db in db_paths:
        scanned_db_count += 1
        source_db_name = source_db.name

        try:
            last_processed_id = writer.get_last_processed_id(source_db_name)
            src_messages = reader.read_incremental(source_db, last_processed_id)
            total_read += len(src_messages)

            normalized_messages = reader.to_normalized(src_messages, deduper)
            filtered_messages = deduper.filter_new_messages(normalized_messages)

            inserted = writer.write_messages(filtered_messages)
            total_inserted += inserted

            new_last_id = src_messages[-1].msg_id if src_messages else last_processed_id
            writer.update_last_processed_id(source_db_name, new_last_id)

            logger.info(
                "source=%s last_processed=%s read=%s deduped=%s inserted=%s new_last_processed=%s",
                source_db_name,
                last_processed_id,
                len(src_messages),
                len(filtered_messages),
                inserted,
                new_last_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed processing source DB %s: %s", source_db_name, exc)

    result = {
        "scanned_db_count": scanned_db_count,
        "total_read": total_read,
        "total_inserted": total_inserted,
    }
    logger.info("run_once finished: %s", result)
    return result


def run_forever(config: CollectorConfig | None = None) -> None:
    config = config or CollectorConfig()
    logger = setup_logger("mac_wechat_incremental_collector", config.log_file, config.log_level)

    logger.info("Starting collector loop, interval=%s seconds", config.run_interval_seconds)
    while True:
        start_ts = time.time()
        run_once(config)

        elapsed = time.time() - start_ts
        sleep_seconds = max(1, config.run_interval_seconds - int(elapsed))
        time.sleep(sleep_seconds)


def run_with_apscheduler(config: CollectorConfig | None = None) -> None:
    """Optional APScheduler mode."""
    config = config or CollectorConfig()
    logger = setup_logger("mac_wechat_incremental_collector", config.log_file, config.log_level)
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except Exception as exc:  # noqa: BLE001
        logger.error("APScheduler is not installed, fallback to run_forever(). reason=%s", exc)
        run_forever(config)
        return

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(run_once, "interval", seconds=config.run_interval_seconds, args=[config], max_instances=1, coalesce=True)
    logger.info("APScheduler started, interval=%s seconds", config.run_interval_seconds)
    scheduler.start()


if __name__ == "__main__":
    run_forever(CollectorConfig())
