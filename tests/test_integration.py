"""統合テスト"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.writer.markdown_gen import MarkdownGenerator
from src.delivery.html_converter import HTMLConverter
from src.feedback.updater import FrontmatterUpdater


class TestPipelineIntegration:
    """パイプラインの主要ステップの統合テスト。"""

    def test_markdown_to_html_flow(self, tmp_path):
        """Markdown生成 → HTML変換の一連フロー。"""
        config = {
            "knowledge_base": {"daily_dir": str(tmp_path)},
            "delivery": {"gmail": {"sender": "test@example.com"}},
        }

        stories = [
            {
                "title": "Original Title",
                "story_title": "AIの進化が止まらない？3つの注目ポイント",
                "story_body": "**注目すべき**テクノロジーの最新動向を解説します。",
                "source": "TechCrunch",
                "category": "海外テック",
                "url": "https://example.com/article",
                "tags": ["LLM", "業務効率化"],
                "framework": "ヒーローズジャーニー",
                "score": 18,
            },
            {
                "title": "Second Article",
                "story_title": "日本企業のAI導入は遅れている？現状と課題",
                "story_body": "日本のAI導入率について分析します。",
                "source": "ITmedia",
                "category": "国内テック",
                "url": "https://example.com/article2",
                "tags": ["業務効率化"],
                "framework": "PAS",
                "score": 15,
            },
        ]

        insight = "本日のAIニュースからは、LLMの進化と日本市場への影響が共通テーマとして浮かび上がりました。"

        # Step 1: Markdown生成
        md_gen = MarkdownGenerator(config)
        md_path = md_gen.generate("2024-01-15", stories, insight)
        assert Path(md_path).exists()

        md_content = Path(md_path).read_text(encoding="utf-8")
        assert "AIの進化が止まらない" in md_content
        assert "日本企業のAI導入" in md_content

        # Step 2: HTML変換
        converter = HTMLConverter(config)
        html = converter.convert("2024-01-15", stories, insight)
        assert "AIの進化が止まらない" in html
        assert "<strong>注目すべき</strong>" in html
        assert "test@example.com" in html

        # Step 3: プレーンテキスト変換
        plain = converter.convert_to_plain_text("2024-01-15", stories, insight)
        assert "AIの進化が止まらない" in plain

    def test_reaction_flow(self, tmp_path):
        """リアクション → Frontmatter更新フロー。"""
        config = {"knowledge_base": {"daily_dir": str(tmp_path)}}

        # Markdown生成
        md_gen = MarkdownGenerator(config)
        stories = [
            {
                "title": "Test",
                "story_title": "テスト",
                "story_body": "本文",
                "source": "Test",
                "category": "テスト",
                "url": "https://example.com",
                "tags": [],
                "framework": "STAR",
                "score": 10,
            }
        ]
        md_gen.generate("2024-01-15", stories)

        # リアクション更新
        updater = FrontmatterUpdater(config)

        assert updater.update_reaction("2024-01-15", 1, "excellent", 5)
        assert updater.update_reaction("2024-01-15", 1, "good", 4)
        assert updater.update_reaction("2024-01-15", 1, "excellent", 5)

        # 検証
        import frontmatter

        post = frontmatter.load(str(tmp_path / "2024-01-15_ai_news.md"))
        story = post.metadata["stories"][0]
        assert story["reactions"]["excellent"] == 2
        assert story["reactions"]["good"] == 1
        assert post.metadata["total_reactions"] == 3
