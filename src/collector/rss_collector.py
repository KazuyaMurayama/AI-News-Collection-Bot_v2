"""RSSフィード収集モジュール"""

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser

logger = logging.getLogger(__name__)

USER_AGENT = "AI-News-Bot/1.0"


def _strip_html(text: str) -> str:
    """HTMLタグを除去する。"""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:1500]


def _parse_date(entry: dict) -> str:
    """エントリの公開日時をISO 8601形式にパースする。"""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                from time import mktime

                dt = datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass

    for field in ("published", "updated"):
        raw = entry.get(field)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.isoformat()
            except Exception:
                pass
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                return dt.isoformat()
            except Exception:
                pass

    return datetime.now(timezone.utc).isoformat()


class RSSCollector:
    """RSSフィードからニュースを収集する。"""

    def collect(self, source: dict) -> list[dict]:
        """単一のRSSソースから記事を収集する。"""
        url = source["url"]
        feed = feedparser.parse(url, agent=USER_AGENT)

        if feed.bozo and not feed.entries:
            logger.warning("RSSパースエラー (%s): %s", source["name"], feed.bozo_exception)
            return []

        articles: list[dict] = []
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            summary = ""
            if entry.get("summary"):
                summary = _strip_html(entry["summary"])
            elif entry.get("description"):
                summary = _strip_html(entry["description"])

            article = {
                "title": title,
                "url": link,
                "summary": summary,
                "published": _parse_date(entry),
                "source": source["name"],
                "category": source.get("category", ""),
                "language": source.get("language", "en"),
            }
            articles.append(article)

        return articles
