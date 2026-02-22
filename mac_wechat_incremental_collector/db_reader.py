"""Read incremental messages from macOS WeChat SQLite DB files."""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mac_wechat_incremental_collector.config import CollectorConfig
from mac_wechat_incremental_collector.db_writer import NormalizedMessage
from mac_wechat_incremental_collector.message_deduper import MessageDeduper


@dataclass(slots=True)
class SourceMessage:
    msg_id: int
    sender: str
    group_name: str
    content: str
    create_time: datetime
    source_db: str


class WeChatDBReader:
    """Safe reader that copies source DBs before querying to avoid lock conflicts."""

    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self.config.db_copy_dir.mkdir(parents=True, exist_ok=True)

    def scan_source_dbs(self) -> list[Path]:
        return sorted(self.config.wechat_db_dir.glob(self.config.source_db_glob))

    def read_incremental(self, source_db_path: Path, last_processed_id: int, limit: int = 5000) -> list[SourceMessage]:
        """Read messages where msg_id > last_processed_id."""
        copied_path = self._copy_db_for_read(source_db_path)

        query = f"""
            SELECT
                {self.config.source_msg_id_col} AS msg_id,
                {self.config.source_sender_col} AS sender,
                {self.config.source_group_col} AS group_name,
                {self.config.source_content_col} AS content,
                {self.config.source_create_time_col} AS create_time
            FROM {self.config.source_table}
            WHERE {self.config.source_msg_id_col} > ?
            ORDER BY {self.config.source_msg_id_col} ASC
            LIMIT ?
        """

        conn = sqlite3.connect(copied_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query, (last_processed_id, limit)).fetchall()
        finally:
            conn.close()
            copied_path.unlink(missing_ok=True)

        messages: list[SourceMessage] = []
        for row in rows:
            messages.append(
                SourceMessage(
                    msg_id=int(row["msg_id"]),
                    sender=str(row["sender"] or "unknown"),
                    group_name=str(row["group_name"] or "unknown_group"),
                    content=str(row["content"] or ""),
                    create_time=self._normalize_time(row["create_time"]),
                    source_db=source_db_path.name,
                )
            )
        return messages

    def to_normalized(self, src_messages: list[SourceMessage], deduper: MessageDeduper) -> list[NormalizedMessage]:
        normalized: list[NormalizedMessage] = []
        for msg in src_messages:
            message_hash = deduper.build_hash(msg.sender, msg.content, msg.create_time)
            normalized.append(
                NormalizedMessage(
                    msg_id=msg.msg_id,
                    sender=msg.sender,
                    group_name=msg.group_name,
                    content=msg.content,
                    create_time=msg.create_time,
                    message_hash=message_hash,
                    source_db=msg.source_db,
                    source_type="db_read",
                )
            )
        return normalized

    def _copy_db_for_read(self, source_path: Path) -> Path:
        fd, tmp_name = tempfile.mkstemp(prefix=f"{source_path.stem}_", suffix=".db", dir=self.config.db_copy_dir)
        os.close(fd)
        Path(tmp_name).unlink(missing_ok=True)
        shutil.copy2(source_path, tmp_name)
        Path(tmp_name).chmod(0o600)
        return Path(tmp_name)

    @staticmethod
    def _normalize_time(raw_time: object) -> datetime:
        if isinstance(raw_time, int):
            return datetime.fromtimestamp(raw_time)
        if isinstance(raw_time, float):
            return datetime.fromtimestamp(int(raw_time))
        if isinstance(raw_time, str):
            try:
                return datetime.fromisoformat(raw_time)
            except ValueError:
                return datetime.fromtimestamp(int(raw_time))
        raise ValueError(f"Unsupported create_time format: {raw_time!r}")
