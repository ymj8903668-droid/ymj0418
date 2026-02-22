"""Stock matcher based on code and name lookup."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import akshare as ak

logger = logging.getLogger(__name__)

_STOCK_CODE_RE = re.compile(r"\b\d{6}\b")


@dataclass(slots=True)
class StockInfo:
    code: str
    name: str


class StockMatcher:
    def __init__(self) -> None:
        self.stock_by_code: dict[str, StockInfo] = {}
        self.stock_by_name: dict[str, StockInfo] = {}
        self._load_stock_pool()

    def _load_stock_pool(self) -> None:
        fallback = [
            StockInfo("000001", "平安银行"),
            StockInfo("300750", "宁德时代"),
            StockInfo("300308", "中际旭创"),
        ]

        try:
            stock_df = ak.stock_info_a_code_name()
            for _, row in stock_df.iterrows():
                code = str(row["code"]).zfill(6)
                name = str(row["name"]).strip()
                info = StockInfo(code=code, name=name)
                self.stock_by_code[code] = info
                self.stock_by_name[name] = info
            logger.info("Loaded %s stocks from akshare.", len(self.stock_by_code))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load stocks from akshare: %s. Using fallback set.", exc)
            for info in fallback:
                self.stock_by_code[info.code] = info
                self.stock_by_name[info.name] = info

    def match(self, text: str) -> list[dict[str, str]]:
        """Match stock mentions by 6-digit code or known stock names."""
        text = text or ""
        results: dict[str, dict[str, str]] = {}

        for code in _STOCK_CODE_RE.findall(text):
            info = self.stock_by_code.get(code)
            if info:
                results[code] = {
                    "stock_code": info.code,
                    "stock_name": info.name,
                    "matched_text": code,
                }

        for name, info in self.stock_by_name.items():
            if name and name in text:
                results[info.code] = {
                    "stock_code": info.code,
                    "stock_name": info.name,
                    "matched_text": name,
                }

        return list(results.values())
