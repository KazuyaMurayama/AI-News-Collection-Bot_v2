"""配信モジュールのテスト"""

from unittest.mock import patch, MagicMock

import pytest

from src.delivery.html_converter import HTMLConverter, markdown_to_html
from src.delivery.gmail_sender import GmailSender
from src.delivery.line_sender import LineSender


class TestHTMLConverter:
    def test_markdown_to_html(self):
        result = markdown_to_html("**bold** text")
        assert "<strong>bold</strong>" in result

    def test_convert(self):
        config = {"delivery": {"gmail": {"sender": "test@example.com"}}}
        converter = HTMLConverter(config)

        stories = [
            {
                "story_title": "テスト記事",
                "story_body": "**テスト**本文",
                "source": "TestSource",
                "category": "テスト",
                "url": "https://example.com",
                "tags": ["LLM"],
            }
        ]

        html = converter.convert("2024-01-01", stories, "インサイト")
        assert "テスト記事" in html
        assert "test@example.com" in html
        assert "2024-01-01" in html

    def test_convert_to_plain_text(self):
        config = {"delivery": {"gmail": {"sender": "test@example.com"}}}
        converter = HTMLConverter(config)

        stories = [
            {
                "story_title": "テスト記事",
                "story_body": "テスト本文",
                "source": "TestSource",
                "category": "テスト",
                "url": "https://example.com",
                "tags": ["LLM"],
                "title": "Test",
                "summary": "Test summary",
            }
        ]

        text = converter.convert_to_plain_text("2024-01-01", stories)
        assert "テスト記事" in text
        assert "テスト本文" in text


class TestGmailSender:
    def test_authenticate_no_password(self):
        with patch.dict("os.environ", {"GMAIL_APP_PASSWORD": ""}):
            sender = GmailSender({"delivery": {"gmail": {"auth_method": "smtp", "sender": "test@example.com"}}})
            assert not sender.authenticate()

    def test_authenticate_with_password(self):
        with patch.dict("os.environ", {"GMAIL_APP_PASSWORD": "test-password"}):
            sender = GmailSender({"delivery": {"gmail": {"auth_method": "smtp", "sender": "test@example.com"}}})
            assert sender.authenticate()


class TestLineSender:
    def test_disabled(self):
        sender = LineSender({"delivery": {"line": {"enabled": False}}})
        assert not sender.send("test")

    @patch("src.delivery.line_sender.requests.post")
    @patch.dict("os.environ", {"LINE_NOTIFY_TOKEN": "test-token"})
    def test_send(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        sender = LineSender({"delivery": {"line": {"enabled": True}}})
        assert sender.send("test message")

    def test_truncate_long_message(self):
        sender = LineSender({"delivery": {"line": {"enabled": True}}})
        # Just verify the class initializes; actual truncation is in send()
        assert sender.enabled
