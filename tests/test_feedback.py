"""フィードバックモジュールのテスト"""

import pytest
import frontmatter

from src.feedback.email_processor import REACTION_PATTERN, REACTION_RATINGS
from src.feedback.updater import FrontmatterUpdater


class TestReactionPattern:
    def test_pattern_match_english(self):
        subject = "[AI-NEWS-REACT] 2024-01-15 / Story 3 / excellent"
        match = REACTION_PATTERN.search(subject)
        assert match is not None
        assert match.group(1) == "2024-01-15"
        assert match.group(2) == "3"
        assert match.group(3) == "excellent"

    def test_pattern_match_japanese(self):
        subject = "[AI-NEWS-REACT] 2024-01-15 / 記事 2 / good"
        match = REACTION_PATTERN.search(subject)
        assert match is not None
        assert match.group(2) == "2"
        assert match.group(3) == "good"

    def test_pattern_no_match(self):
        subject = "Regular email subject"
        match = REACTION_PATTERN.search(subject)
        assert match is None

    def test_reaction_ratings(self):
        assert REACTION_RATINGS["excellent"] == 5
        assert REACTION_RATINGS["good"] == 4
        assert REACTION_RATINGS["read_later"] == 3
        assert REACTION_RATINGS["so_so"] == 2


class TestFrontmatterUpdater:
    def test_update_reaction(self, tmp_path):
        config = {"knowledge_base": {"daily_dir": str(tmp_path)}}

        # Create test markdown
        md_content = "Test content"
        metadata = {
            "date": "2024-01-15",
            "total_reactions": 0,
            "stories": [
                {
                    "id": 1,
                    "original_title": "Test",
                    "reactions": {"excellent": 0, "good": 0, "so_so": 0, "read_later": 0},
                    "rating": 0,
                }
            ],
        }
        post = frontmatter.Post(md_content, **metadata)
        md_path = tmp_path / "2024-01-15_ai_news.md"
        md_path.write_text(frontmatter.dumps(post))

        updater = FrontmatterUpdater(config)
        result = updater.update_reaction("2024-01-15", 1, "excellent", 5)
        assert result

        # Verify update
        updated = frontmatter.load(str(md_path))
        assert updated.metadata["stories"][0]["reactions"]["excellent"] == 1
        assert updated.metadata["total_reactions"] == 1

    def test_update_nonexistent_file(self, tmp_path):
        config = {"knowledge_base": {"daily_dir": str(tmp_path)}}
        updater = FrontmatterUpdater(config)
        result = updater.update_reaction("9999-01-01", 1, "good", 4)
        assert not result

    def test_update_invalid_story_id(self, tmp_path):
        config = {"knowledge_base": {"daily_dir": str(tmp_path)}}

        metadata = {"date": "2024-01-15", "total_reactions": 0, "stories": []}
        post = frontmatter.Post("content", **metadata)
        md_path = tmp_path / "2024-01-15_ai_news.md"
        md_path.write_text(frontmatter.dumps(post))

        updater = FrontmatterUpdater(config)
        result = updater.update_reaction("2024-01-15", 99, "good", 4)
        assert not result
