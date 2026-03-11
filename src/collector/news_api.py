"""NewsAPI / Hacker News API 収集モジュール"""

import logging
import os
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)


class NewsAPICollector:
    """NewsAPI.org からニュースを収集する。"""

    def collect(self, source: dict) -> list[dict]:
        api_key = os.environ.get("NEWS_API_KEY", "")
        if not api_key:
            logger.info("NEWS_API_KEY が未設定のためスキップ")
            return []

        base_url = source.get("url", "https://newsapi.org/v2")
        query = source.get("query", "artificial intelligence")
        from_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        resp = requests.get(
            f"{base_url}/everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 20,
                "apiKey": api_key,
            },
            headers={"User-Agent": "AI-News-Bot/1.0"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        articles: list[dict] = []
        for item in data.get("articles", []):
            title = item.get("title", "")
            if not title or "[Removed]" in title:
                continue
            articles.append(
                {
                    "title": title,
                    "url": item.get("url", ""),
                    "summary": (item.get("description") or "")[:1500],
                    "published": item.get("publishedAt", ""),
                    "source": source.get("name", "NewsAPI"),
                    "category": source.get("category", "海外テック"),
                    "language": source.get("language", "en"),
                }
            )
        return articles


class HackerNewsCollector:
    """Hacker News Algolia API からニュースを収集する。"""

    def collect(self, source: dict) -> list[dict]:
        base_url = source.get("url", "http://hn.algolia.com/api/v1")
        query = source.get("query", "AI OR LLM OR GPT")

        resp = requests.get(
            f"{base_url}/search_by_date",
            params={
                "query": query,
                "tags": "story",
                "numericFilters": "points>10",
                "hitsPerPage": 20,
            },
            headers={"User-Agent": "AI-News-Bot/1.0"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        articles: list[dict] = []
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            if not title:
                continue
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            points = hit.get("points", 0)
            comments = hit.get("num_comments", 0)
            summary = f"Points: {points} | Comments: {comments}"
            if hit.get("story_text"):
                summary += f" | {hit['story_text'][:1000]}"

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": summary[:1500],
                    "published": hit.get("created_at", ""),
                    "source": source.get("name", "Hacker News"),
                    "category": source.get("category", "海外テック"),
                    "language": source.get("language", "en"),
                }
            )
        return articles
