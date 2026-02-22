"""Keyword based topic matching."""

from __future__ import annotations

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "算力": ["算力", "AIDC", "数据中心", "服务器"],
    "机器人": ["机器人", "人形机器人", "自动化"],
    "半导体": ["半导体", "芯片", "晶圆", "封测"],
    "AI应用": ["AI应用", "AIGC", "大模型", "智能助手"],
    "新能源": ["新能源", "光伏", "风电", "储能", "锂电"],
}


class TopicMatcher:
    def __init__(self, topic_keywords: dict[str, list[str]] | None = None) -> None:
        self.topic_keywords = topic_keywords or TOPIC_KEYWORDS

    def match(self, text: str) -> list[dict[str, str]]:
        text = text or ""
        results: list[dict[str, str]] = []
        for topic, keywords in self.topic_keywords.items():
            for kw in keywords:
                if kw in text:
                    results.append({"topic_name": topic, "matched_keyword": kw})
                    break
        return results
