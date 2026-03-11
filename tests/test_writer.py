"""コンテンツ生成モジュールのテスト"""

import pytest

from src.writer.storyteller import (
    _contains_japanese,
    extract_title_and_body,
    _select_framework_by_keywords,
    select_framework,
    FRAMEWORK_KEYWORDS,
)
from src.writer.markdown_gen import MarkdownGenerator


class TestJapaneseValidation:
    def test_contains_japanese_hiragana(self):
        assert _contains_japanese("これはテストです。")

    def test_contains_japanese_katakana(self):
        assert _contains_japanese("テスト文字列")

    def test_contains_japanese_kanji(self):
        assert _contains_japanese("日本語のテスト")

    def test_no_japanese(self):
        assert not _contains_japanese("This is English only")

    def test_empty_string(self):
        assert not _contains_japanese("")

    def test_mixed_with_low_ratio(self):
        # Very long English with tiny Japanese
        text = "A" * 100 + "あ"
        assert not _contains_japanese(text, min_ratio=0.1)


class TestExtractTitleAndBody:
    def test_basic(self):
        text = "My Title\n\nBody text here."
        title, body = extract_title_and_body(text)
        assert title == "My Title"
        assert "Body text here." in body

    def test_bold_title(self):
        text = "**Bold Title**\n\nBody"
        title, body = extract_title_and_body(text)
        assert title == "Bold Title"

    def test_heading_title(self):
        text = "## Heading Title\n\nBody"
        title, body = extract_title_and_body(text)
        assert title == "Heading Title"

    def test_empty_lines_before(self):
        text = "\n\n\nActual Title\n\nBody"
        title, body = extract_title_and_body(text)
        assert title == "Actual Title"


class TestFrameworkSelection:
    def test_star_keywords(self):
        result = _select_framework_by_keywords("企業がAIを導入", "ROI向上の実績")
        assert result == "STAR"

    def test_heros_journey_keywords(self):
        result = _select_framework_by_keywords("Revolutionary new GPT model released", "breakthrough")
        assert result == "ヒーローズジャーニー"

    def test_bab_keywords(self):
        result = _select_framework_by_keywords("AI効率化update", "ワークフロー自動化")
        assert result == "Before-After-Bridge"

    def test_pas_keywords(self):
        result = _select_framework_by_keywords("AIセキュリティリスク", "脆弱性とバイアスの課題")
        assert result == "PAS"

    def test_no_match(self):
        result = _select_framework_by_keywords("generic topic", "no keywords here")
        assert result is None


class TestMarkdownGenerator:
    def test_generate(self, tmp_path):
        config = {"knowledge_base": {"daily_dir": str(tmp_path)}}
        gen = MarkdownGenerator(config)

        stories = [
            {
                "title": "Test Article",
                "story_title": "テスト記事タイトル",
                "story_body": "テスト本文",
                "source": "TestSource",
                "category": "テスト",
                "url": "https://example.com",
                "tags": ["LLM", "研究・学術"],
                "framework": "STAR",
                "score": 15,
            }
        ]

        path = gen.generate("2024-01-01", stories, "テストインサイト")
        assert (tmp_path / "2024-01-01_ai_news.md").exists()

        content = (tmp_path / "2024-01-01_ai_news.md").read_text()
        assert "テスト記事タイトル" in content
        assert "テストインサイト" in content
