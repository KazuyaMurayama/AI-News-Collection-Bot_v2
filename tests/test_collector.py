"""ニュース収集モジュールのテスト"""

from unittest.mock import patch, MagicMock

import pytest

from src.collector.rss_collector import RSSCollector, _strip_html, _parse_date
from src.collector.news_api import NewsAPICollector, HackerNewsCollector
from src.collector.selector import ArticleSelector


class TestRSSCollector:
    def test_strip_html(self):
        assert _strip_html("<p>Hello <b>World</b></p>") == "Hello World"
        assert _strip_html("") == ""

    def test_strip_html_truncate(self):
        long_text = "<p>" + "a" * 2000 + "</p>"
        result = _strip_html(long_text)
        assert len(result) <= 1500

    def test_parse_date_fallback(self):
        result = _parse_date({})
        assert "T" in result  # ISO format

    @patch("src.collector.rss_collector.feedparser.parse")
    def test_collect_basic(self, mock_parse):
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[
                MagicMock(
                    get=lambda key, default="": {
                        "title": "Test Article",
                        "link": "https://example.com/test",
                        "summary": "Test summary",
                    }.get(key, default),
                    **{
                        "title": "Test Article",
                        "link": "https://example.com/test",
                        "summary": "Test summary",
                    },
                )
            ],
        )
        # Simpler approach: mock at higher level
        collector = RSSCollector()
        source = {
            "name": "Test",
            "url": "https://example.com/feed",
            "category": "テスト",
            "language": "en",
        }
        # Just verify no crash with actual feedparser mock
        with patch("src.collector.rss_collector.feedparser") as fp:
            fp.parse.return_value = type("Feed", (), {
                "bozo": False,
                "entries": [
                    {
                        "title": "Test Article",
                        "link": "https://example.com",
                        "summary": "<p>Summary</p>",
                        "published_parsed": None,
                    }
                ],
            })()
            articles = collector.collect(source)
            assert len(articles) == 1
            assert articles[0]["title"] == "Test Article"

    @patch("src.collector.rss_collector.feedparser")
    def test_collect_empty_feed(self, mock_fp):
        mock_fp.parse.return_value = type("Feed", (), {
            "bozo": True,
            "bozo_exception": Exception("test"),
            "entries": [],
        })()
        collector = RSSCollector()
        result = collector.collect({"name": "Test", "url": "https://example.com/feed"})
        assert result == []


class TestNewsAPICollector:
    @patch.dict("os.environ", {"NEWS_API_KEY": ""})
    def test_no_api_key(self):
        collector = NewsAPICollector()
        result = collector.collect({"url": "https://newsapi.org/v2"})
        assert result == []

    @patch("src.collector.news_api.requests.get")
    @patch.dict("os.environ", {"NEWS_API_KEY": "test-key"})
    def test_collect(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "articles": [
                    {
                        "title": "AI News",
                        "url": "https://example.com",
                        "description": "Test",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    },
                    {
                        "title": "[Removed]",
                        "url": "",
                        "description": "",
                        "publishedAt": "",
                    },
                ]
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()
        collector = NewsAPICollector()
        result = collector.collect({"url": "https://newsapi.org/v2", "query": "AI"})
        assert len(result) == 1
        assert result[0]["title"] == "AI News"


class TestHackerNewsCollector:
    @patch("src.collector.news_api.requests.get")
    def test_collect(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "hits": [
                    {
                        "title": "HN Article",
                        "url": "https://example.com",
                        "points": 100,
                        "num_comments": 50,
                        "objectID": "123",
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                ]
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()
        collector = HackerNewsCollector()
        result = collector.collect({"url": "http://hn.algolia.com/api/v1", "query": "AI"})
        assert len(result) == 1
        assert "Points: 100" in result[0]["summary"]


class TestArticleSelector:
    def test_deduplicate(self):
        selector = ArticleSelector({"claude": {}, "selection": {"select_count": 5}})
        articles = [
            {"title": "Article A", "url": "https://a.com"},
            {"title": "Article A", "url": "https://b.com"},  # dup title
            {"title": "Article B", "url": "https://a.com"},  # dup url
            {"title": "Article C", "url": "https://c.com"},
        ]
        unique = selector._deduplicate(articles)
        assert len(unique) == 2

    def test_fallback_sort(self):
        selector = ArticleSelector({"claude": {}, "selection": {"select_count": 5}})
        articles = [
            {"title": "Old", "published": "2024-01-01T00:00:00+00:00"},
            {"title": "New", "published": "2024-06-01T00:00:00+00:00"},
        ]
        sorted_articles = selector._fallback_sort(articles)
        assert sorted_articles[0]["title"] == "New"
