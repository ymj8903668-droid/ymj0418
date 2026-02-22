"""Message parsing utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_raw_message(raw_row: dict[str, Any]) -> dict[str, Any]:
    """Normalize source row into target message fields."""
    return {
        "raw_id": raw_row["id"],
        "sender": (raw_row.get("sender") or "unknown").strip(),
        "group_name": (raw_row.get("group_name") or "unknown_group").strip(),
        "content": (raw_row.get("content") or "").strip(),
        "sent_at": _ensure_datetime(raw_row.get("sent_at")),
    }


def _ensure_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError(f"Unsupported sent_at value: {value!r}")
