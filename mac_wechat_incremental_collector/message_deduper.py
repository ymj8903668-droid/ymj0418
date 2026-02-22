"""Deduplication for normalized messages."""

from __future__ import annotations

import hashlib
from datetime import datetime

from mac_wechat_incremental_collector.db_writer import DBWriter, NormalizedMessage


class MessageDeduper:
    """Create robust hashes and filter duplicates before persistence."""

    def __init__(self, writer: DBWriter) -> None:
        self.writer = writer

    @staticmethod
    def build_hash(sender: str, content: str, create_time: datetime) -> str:
        raw = f"{sender.strip()}|{content.strip()}|{create_time.isoformat()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def filter_new_messages(self, messages: list[NormalizedMessage]) -> list[NormalizedMessage]:
        unique_by_hash: dict[str, NormalizedMessage] = {}
        for msg in messages:
            unique_by_hash[msg.message_hash] = msg

        filtered: list[NormalizedMessage] = []
        for msg_hash, msg in unique_by_hash.items():
            if not self.writer.message_hash_exists(msg_hash):
                filtered.append(msg)
        return filtered
