"""Configuration for macOS WeChat incremental collector."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CollectorConfig:
    """Runtime settings.

    All fields can be overridden with environment variables.
    """

    # Source (macOS WeChat SQLite folder + db file scan pattern)
    wechat_db_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "WECHAT_DB_DIR",
                str(Path.home() / "Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat"),
            )
        )
    )
    source_db_glob: str = os.getenv("WECHAT_DB_GLOB", "**/MSG*.db")
    source_table: str = os.getenv("WECHAT_SOURCE_TABLE", "message_table")

    # SQL column mapping in source table
    source_msg_id_col: str = os.getenv("WECHAT_MSG_ID_COL", "msg_id")
    source_sender_col: str = os.getenv("WECHAT_SENDER_COL", "sender")
    source_group_col: str = os.getenv("WECHAT_GROUP_COL", "group_name")
    source_content_col: str = os.getenv("WECHAT_CONTENT_COL", "content")
    source_create_time_col: str = os.getenv("WECHAT_CREATE_TIME_COL", "create_time")

    # Sink database settings
    target_db_type: str = os.getenv("TARGET_DB_TYPE", "sqlite")  # sqlite | postgres
    target_sqlite_path: Path = field(default_factory=lambda: Path(os.getenv("TARGET_SQLITE_PATH", "collector_output.db")))
    target_postgres_dsn: str = os.getenv("TARGET_POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/alpha_information_system")

    # Runtime behavior
    run_interval_seconds: int = int(os.getenv("RUN_INTERVAL_SECONDS", "120"))
    db_copy_dir: Path = field(default_factory=lambda: Path(os.getenv("DB_COPY_DIR", "/tmp/wechat_db_copies")))
    log_file: Path = field(default_factory=lambda: Path(os.getenv("LOG_FILE", "mac_wechat_incremental_collector.log")))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> None:
        if self.run_interval_seconds < 60:
            raise ValueError("RUN_INTERVAL_SECONDS must be >= 60 for stable long-running collection")
        if self.target_db_type not in {"sqlite", "postgres"}:
            raise ValueError("TARGET_DB_TYPE must be one of: sqlite, postgres")
