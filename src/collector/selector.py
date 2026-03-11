"""Claude APIスコアリング・記事選定モジュール"""

import json
import logging
import os
from datetime import datetime, timezone

import anthropic

from ..utils.retry import with_retry

logger = logging.getLogger(__name__)


class ArticleSelector:
    """Claude APIを使って記事をスコアリングし、上位を選定する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.claude_config = config.get("claude", {})
        self.selection_config = config.get("selection", {})
        self.select_count = self.selection_config.get("select_count", 5)

    def _deduplicate(self, articles: list[dict]) -> list[dict]:
        """URL完全一致 + タイトル完全一致（小文字化）で重複排除。"""
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[dict] = []

        for article in articles:
            url = article.get("url", "")
            title_lower = article.get("title", "").strip().lower()
            if url in seen_urls or title_lower in seen_titles:
                continue
            seen_urls.add(url)
            if title_lower:
                seen_titles.add(title_lower)
            unique.append(article)

        return unique

    @with_retry(max_attempts=3, backoff_base=2, retry_on=(Exception,))
    def _score_batch(self, articles: list[dict]) -> list[dict]:
        """Claude APIで記事群をスコアリングする。"""
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

        articles_text = ""
        for i, a in enumerate(articles):
            articles_text += (
                f"\n--- 記事 {i + 1} ---\n"
                f"タイトル: {a['title']}\n"
                f"ソース: {a['source']}\n"
                f"概要: {a.get('summary', '')[:500]}\n"
                f"公開日: {a.get('published', 'N/A')}\n"
            )

        prompt = f"""以下のAI関連ニュース記事を評価し、各記事にスコアを付けてください。

評価基準:
- novelty (先進性, 0-5): 技術的な新しさ
- surprise (意外性, 0-5): 予想外の展開や発見
- practicality (実用性, 0-5): ビジネスや実務への適用可能性
- japan_relevance (日本企業関連性, 0-3): 日本市場・企業への関連度
- freshness (鮮度, 0-2): 情報の新しさ

以下のJSON形式で回答してください:
[
  {{"index": 0, "novelty": 4, "surprise": 3, "practicality": 5, "japan_relevance": 2, "freshness": 2, "total": 16, "reason": "理由"}},
  ...
]

記事一覧:
{articles_text}
"""

        response = client.messages.create(
            model=self.claude_config.get("model", "claude-sonnet-4-20250514"),
            max_tokens=4096,
            temperature=self.claude_config.get("scoring_temperature", 0.3),
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        # JSONブロックを抽出
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        scores = json.loads(content.strip())

        for score in scores:
            idx = score.get("index", 0)
            if 0 <= idx < len(articles):
                articles[idx]["score"] = score.get("total", 0)
                articles[idx]["score_detail"] = score
                articles[idx]["score_reason"] = score.get("reason", "")

        return articles

    def _fallback_sort(self, articles: list[dict]) -> list[dict]:
        """API失敗時のフォールバック: 公開日時の新しい順。"""

        def parse_date(a: dict) -> datetime:
            try:
                raw = a.get("published", "")
                if raw:
                    return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except Exception:
                pass
            return datetime.min.replace(tzinfo=timezone.utc)

        return sorted(articles, key=parse_date, reverse=True)

    def select(self, articles: list[dict]) -> list[dict]:
        """記事を選定して上位N件を返す。"""
        unique = self._deduplicate(articles)
        logger.info("重複排除後: %d 記事", len(unique))

        if not unique:
            return []

        try:
            scored = self._score_batch(unique[:30])
            scored.sort(key=lambda a: a.get("score", 0), reverse=True)
        except Exception as e:
            logger.error("スコアリング失敗、フォールバック使用: %s", e)
            scored = self._fallback_sort(unique)

        selected = scored[: self.select_count]
        logger.info("選定: %d 記事", len(selected))
        return selected
