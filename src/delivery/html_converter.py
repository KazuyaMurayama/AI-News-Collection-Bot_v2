"""Markdown→HTML変換・テンプレート適用モジュール"""

import logging
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "writer" / "templates"


def markdown_to_html(text: str) -> str:
    """MarkdownテキストをHTMLに変換する。"""
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )


class HTMLConverter:
    """ストーリーをHTMLメール形式に変換する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=False,
        )

    def convert(
        self,
        date_str: str,
        stories: list[dict],
        insight: str = "",
    ) -> str:
        """ストーリーリストをHTMLメールに変換する。"""
        processed_stories = []
        for story in stories:
            processed = dict(story)
            body = story.get("story_body", story.get("summary", ""))
            processed["story_body_html"] = markdown_to_html(body)
            if not processed.get("tags"):
                processed["tags"] = []
            processed_stories.append(processed)

        sender = (
            self.config.get("delivery", {})
            .get("gmail", {})
            .get("sender", "")
        )

        template = self.env.get_template("email_template.html")
        html = template.render(
            date=date_str,
            stories=processed_stories,
            insight=insight,
            insight_html=markdown_to_html(insight) if insight else "",
            sender=sender,
        )

        return html

    def convert_to_plain_text(
        self,
        date_str: str,
        stories: list[dict],
        insight: str = "",
    ) -> str:
        """プレーンテキスト版を生成する。"""
        parts: list[str] = []
        parts.append(f"AI ニュース デイリーダイジェスト - {date_str}")
        parts.append("=" * 50)

        for i, story in enumerate(stories):
            parts.append(f"\n■ 記事 {i + 1}: {story.get('story_title', story.get('title', ''))}")
            parts.append(f"  ソース: {story.get('source', '')}")
            parts.append(f"  カテゴリ: {story.get('category', '')}")
            parts.append(f"  タグ: {', '.join(story.get('tags', []))}")
            parts.append(f"  元記事: {story.get('url', '')}")
            parts.append("")
            body = story.get("story_body", story.get("summary", ""))
            parts.append(body)
            parts.append("-" * 50)

        if insight:
            parts.append("\n■ 本日のインサイト")
            parts.append(insight)

        parts.append("\n" + "=" * 50)
        parts.append("AI ニュース Bot v2.0 | Claude API で自動生成")

        return "\n".join(parts)
