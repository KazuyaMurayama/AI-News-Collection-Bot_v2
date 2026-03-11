"""YAML Frontmatter付きMarkdown生成モジュール"""

import logging
from datetime import datetime
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """日次レポートのMarkdownを生成する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        kb_config = config.get("knowledge_base", {})
        self.daily_dir = Path(kb_config.get("daily_dir", "./knowledge_base/daily"))
        self.daily_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        date_str: str,
        stories: list[dict],
        insight: str = "",
    ) -> str:
        """Markdown日次レポートを生成し、ファイルに保存する。"""
        metadata = {
            "title": f"AIニュースダイジェスト {date_str}",
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "num_stories": len(stories),
            "total_reactions": 0,
            "stories": [],
        }

        body_parts: list[str] = []
        body_parts.append(f"# AIニュースダイジェスト {date_str}\n")

        for i, story in enumerate(stories):
            story_meta = {
                "id": i + 1,
                "original_title": story.get("title", ""),
                "source": story.get("source", ""),
                "url": story.get("url", ""),
                "category": story.get("category", ""),
                "tags": story.get("tags", []),
                "framework": story.get("framework", ""),
                "score": story.get("score", 0),
                "reactions": {
                    "excellent": 0,
                    "good": 0,
                    "so_so": 0,
                    "read_later": 0,
                },
                "rating": 0,
            }
            metadata["stories"].append(story_meta)

            story_title = story.get("story_title", story.get("title", ""))
            story_body = story.get("story_body", story.get("summary", ""))

            body_parts.append(f"## 記事 {i + 1}: {story_title}\n")
            body_parts.append(f"**ソース:** {story.get('source', '')} | ")
            body_parts.append(f"**カテゴリ:** {story.get('category', '')} | ")
            tags_str = ", ".join(story.get("tags", []))
            body_parts.append(f"**タグ:** {tags_str}\n")
            body_parts.append(f"**元記事:** [{story.get('title', '')}]({story.get('url', '')})\n")
            body_parts.append(f"{story_body}\n")
            body_parts.append("---\n")

        if insight:
            body_parts.append("## 本日のインサイト\n")
            body_parts.append(f"{insight}\n")

        content = "\n".join(body_parts)

        post = frontmatter.Post(content, **metadata)
        md_text = frontmatter.dumps(post)

        file_path = self.daily_dir / f"{date_str}_ai_news.md"
        file_path.write_text(md_text, encoding="utf-8")
        logger.info("Markdown保存: %s", file_path)

        return str(file_path)
