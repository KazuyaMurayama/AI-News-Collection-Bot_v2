"""タグ検索・全文検索・評価フィルタモジュール"""

import logging
import re
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)


def get_all_articles(daily_dir: str = "./knowledge_base/daily") -> list[dict]:
    """全Markdown Frontmatterからメタデータを抽出する。"""
    articles: list[dict] = []
    daily_path = Path(daily_dir)
    if not daily_path.exists():
        return articles

    for md_file in sorted(daily_path.glob("*_ai_news.md"), reverse=True):
        try:
            post = frontmatter.load(str(md_file))
            date = post.metadata.get("date", "")
            for story in post.metadata.get("stories", []):
                article = {
                    "date": date,
                    "file": str(md_file),
                    **story,
                }
                articles.append(article)
        except Exception as e:
            logger.warning("ファイル読み込みエラー %s: %s", md_file, e)

    return articles


def search_by_tag(tag: str, daily_dir: str = "./knowledge_base/daily") -> list[dict]:
    """タグ完全一致検索。"""
    all_articles = get_all_articles(daily_dir)
    return [a for a in all_articles if tag in a.get("tags", [])]


def search_fulltext(query: str, daily_dir: str = "./knowledge_base/daily") -> list[dict]:
    """正規表現全文検索。"""
    results: list[dict] = []
    daily_path = Path(daily_dir)
    if not daily_path.exists():
        return results

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    for md_file in sorted(daily_path.glob("*_ai_news.md"), reverse=True):
        try:
            content = md_file.read_text(encoding="utf-8")
            if pattern.search(content):
                post = frontmatter.load(str(md_file))
                date = post.metadata.get("date", "")
                for story in post.metadata.get("stories", []):
                    title = story.get("original_title", "")
                    if pattern.search(title) or pattern.search(str(story.get("tags", []))):
                        results.append({"date": date, "file": str(md_file), **story})
        except Exception as e:
            logger.warning("検索エラー %s: %s", md_file, e)

    return results


def filter_by_rating(
    min_rating: float, daily_dir: str = "./knowledge_base/daily"
) -> list[dict]:
    """評価フィルタ。"""
    all_articles = get_all_articles(daily_dir)
    return [a for a in all_articles if a.get("rating", 0) >= min_rating]
