"""月次サマリー生成モジュール"""

import logging
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import anthropic
import frontmatter as fm

from ..utils.retry import with_retry
from .search import get_all_articles

logger = logging.getLogger(__name__)


class MonthlySummarizer:
    """月次サマリーを生成する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        kb_config = config.get("knowledge_base", {})
        self.daily_dir = kb_config.get("daily_dir", "./knowledge_base/daily")
        self.monthly_dir = Path(kb_config.get("monthly_dir", "./knowledge_base/monthly"))
        self.monthly_dir.mkdir(parents=True, exist_ok=True)
        self.claude_config = config.get("claude", {})

    def generate(self, year: int, month: int) -> str:
        """指定月のサマリーを生成する。"""
        all_articles = get_all_articles(self.daily_dir)

        month_articles = [
            a
            for a in all_articles
            if a.get("date", "").startswith(f"{year}-{month:02d}")
        ]

        if not month_articles:
            logger.info("対象月の記事なし: %d-%02d", year, month)
            return ""

        # タグ集計
        tag_counter: Counter[str] = Counter()
        for a in month_articles:
            for tag in a.get("tags", []):
                tag_counter[tag] += 1

        # 高評価Top5
        rated = sorted(month_articles, key=lambda x: x.get("rating", 0), reverse=True)
        top5 = rated[:5]

        # Claude APIインサイト
        insight = self._generate_insight(month_articles, tag_counter, top5)

        # Markdown生成
        md_content = self._build_markdown(year, month, month_articles, tag_counter, top5, insight)

        # 保存
        file_path = self.monthly_dir / f"{year}-{month:02d}_summary.md"
        metadata = {
            "title": f"月次サマリー {year}年{month}月",
            "year": year,
            "month": month,
            "total_articles": len(month_articles),
            "generated_at": datetime.now().isoformat(),
        }
        post = fm.Post(md_content, **metadata)
        file_path.write_text(fm.dumps(post), encoding="utf-8")
        logger.info("月次サマリー保存: %s", file_path)

        return str(file_path)

    @with_retry(max_attempts=2, backoff_base=2, retry_on=(Exception,))
    def _generate_insight(
        self, articles: list[dict], tag_counter: Counter, top5: list[dict]
    ) -> str:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

        tags_text = ", ".join(f"{tag}({count})" for tag, count in tag_counter.most_common(10))
        top5_text = "\n".join(
            f"- {a.get('original_title', '')} (rating={a.get('rating', 0)})"
            for a in top5
        )

        response = client.messages.create(
            model=self.claude_config.get("model", "claude-sonnet-4-20250514"),
            max_tokens=1500,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"以下の月次データから500-800文字の日本語インサイトを生成してください。\n\n"
                        f"記事数: {len(articles)}\n"
                        f"頻出タグ: {tags_text}\n"
                        f"高評価Top5:\n{top5_text}"
                    ),
                }
            ],
        )
        return response.content[0].text

    def _build_markdown(
        self,
        year: int,
        month: int,
        articles: list[dict],
        tag_counter: Counter,
        top5: list[dict],
        insight: str,
    ) -> str:
        parts: list[str] = []
        parts.append(f"# 月次サマリー {year}年{month}月\n")
        parts.append(f"総記事数: {len(articles)}\n")

        parts.append("## タグ集計\n")
        for tag, count in tag_counter.most_common(15):
            parts.append(f"- {tag}: {count}件")
        parts.append("")

        parts.append("## 高評価Top5\n")
        for i, a in enumerate(top5):
            parts.append(
                f"{i+1}. {a.get('original_title', '')} "
                f"(rating={a.get('rating', 0)}, source={a.get('source', '')})"
            )
        parts.append("")

        parts.append("## インサイト\n")
        parts.append(insight)

        return "\n".join(parts)
