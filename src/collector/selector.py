"""Claude APIスコアリング・記事選定モジュール"""

import json
import logging
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone

import anthropic

from ..utils.retry import with_retry

logger = logging.getLogger(__name__)

# Anthropic AIエージェント関連の判定キーワード（小文字で比較）
ANTHROPIC_DEFAULT_KEYWORDS = [
    "claude code",
    "claude",
    "anthropic",
    "claude-co-work",
    "claude agent",
    "mcp",
    "model context protocol",
    "claude desktop",
    "claude api",
    "claude sonnet",
    "claude opus",
    "claude haiku",
]


class ArticleSelector:
    """Claude APIを使って記事をスコアリングし、上位を選定する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.claude_config = config.get("claude", {})
        self.selection_config = config.get("selection", {})
        self.select_count = self.selection_config.get("select_count", 3)
        self.anthropic_slot_config = self.selection_config.get("anthropic_slot", {})

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """テキストを正規化してトークンに分割する。"""
        text = unicodedata.normalize("NFKC", text).lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return [t for t in text.split() if len(t) > 1]

    @staticmethod
    def _similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
        """2つのトークンリストのコサイン類似度を返す。"""
        if not tokens_a or not tokens_b:
            return 0.0
        counter_a = Counter(tokens_a)
        counter_b = Counter(tokens_b)
        all_keys = set(counter_a) | set(counter_b)
        dot = sum(counter_a.get(k, 0) * counter_b.get(k, 0) for k in all_keys)
        mag_a = sum(v * v for v in counter_a.values()) ** 0.5
        mag_b = sum(v * v for v in counter_b.values()) ** 0.5
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _deduplicate(self, articles: list[dict]) -> list[dict]:
        """URL完全一致 + タイトル完全一致 + 類似度ベースで重複排除。"""
        threshold = self.selection_config.get("dedup_similarity_threshold", 0.8)
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        accepted: list[dict] = []
        accepted_tokens: list[list[str]] = []

        for article in articles:
            url = article.get("url", "")
            title_lower = article.get("title", "").strip().lower()

            # 1. URL完全一致
            if url in seen_urls:
                continue
            # 2. タイトル完全一致
            if title_lower in seen_titles:
                continue

            # 3. タイトル+概要の類似度チェック
            text = f"{article.get('title', '')} {article.get('summary', '')[:200]}"
            tokens = self._tokenize(text)
            is_similar = False
            for prev_tokens in accepted_tokens:
                if self._similarity(tokens, prev_tokens) >= threshold:
                    is_similar = True
                    logger.debug("類似記事を除外: %s", title_lower[:60])
                    break

            if is_similar:
                continue

            seen_urls.add(url)
            if title_lower:
                seen_titles.add(title_lower)
            accepted.append(article)
            accepted_tokens.append(tokens)

        return accepted

    def _is_anthropic_related(self, article: dict) -> bool:
        """記事がAnthropic AIエージェント関連かどうかを判定する。"""
        keywords = self.anthropic_slot_config.get("keywords", ANTHROPIC_DEFAULT_KEYWORDS)
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        category = article.get("category", "").lower()
        text = f"{title} {summary} {category}"

        for kw in keywords:
            kw_lower = kw.lower()
            # 単語境界を考慮（"Claude" が "excluded" にマッチしないように）
            if re.search(r'\b' + re.escape(kw_lower) + r'\b', text):
                return True
        return False

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

    @staticmethod
    def _parse_date(article: dict) -> datetime:
        """記事の公開日をパースする。"""
        try:
            raw = article.get("published", "")
            if raw:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            pass
        return datetime.min.replace(tzinfo=timezone.utc)

    def _filter_by_freshness(self, articles: list[dict]) -> list[dict]:
        """freshness_hours以内の記事のみ残す。公開日が不明な記事も残す。"""
        freshness_hours = self.selection_config.get("freshness_hours", 72)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)

        fresh: list[dict] = []
        for article in articles:
            pub_date = self._parse_date(article)
            # 公開日が不明（datetime.min）の場合は除外せず残す
            if pub_date == datetime.min.replace(tzinfo=timezone.utc):
                fresh.append(article)
            elif pub_date >= cutoff:
                fresh.append(article)
            else:
                logger.debug("古い記事を除外: %s (%s)", article.get("title", "")[:50], pub_date.isoformat())

        return fresh

    def _fallback_sort(self, articles: list[dict]) -> list[dict]:
        """API失敗時のフォールバック: 公開日時の新しい順。"""
        return sorted(articles, key=self._parse_date, reverse=True)

    def select(self, articles: list[dict]) -> list[dict]:
        """記事を選定して上位N件を返す（うち1枠はAnthropic AIエージェント関連）。"""
        unique = self._deduplicate(articles)
        logger.info("重複排除後: %d 記事", len(unique))

        # 直近N時間以内の記事のみに絞り込む
        unique = self._filter_by_freshness(unique)
        logger.info("鮮度フィルタ後: %d 記事", len(unique))

        if not unique:
            return []

        # スコアリング
        try:
            scored = self._score_batch(unique[:30])
            scored.sort(key=lambda a: a.get("score", 0), reverse=True)
        except Exception as e:
            logger.error("スコアリング失敗、フォールバック使用: %s", e)
            scored = self._fallback_sort(unique)

        # Anthropic枠が有効か
        anthropic_enabled = self.anthropic_slot_config.get("enabled", True)
        anthropic_count = self.anthropic_slot_config.get("count", 1)

        if not anthropic_enabled or anthropic_count <= 0:
            # Anthropic枠なし: 従来通り上位N件
            selected = scored[: self.select_count]
            logger.info("選定: %d 記事", len(selected))
            return selected

        # Anthropic関連記事と一般記事を分離
        anthropic_articles = [a for a in scored if self._is_anthropic_related(a)]
        general_articles = [a for a in scored if not self._is_anthropic_related(a)]

        logger.info("Anthropic関連候補: %d 記事, 一般候補: %d 記事",
                     len(anthropic_articles), len(general_articles))

        selected: list[dict] = []

        # 1. Anthropic枠を確保
        anthropic_selected = anthropic_articles[:anthropic_count]
        selected.extend(anthropic_selected)
        if anthropic_selected:
            logger.info("Anthropic枠: %s", [a.get("title", "")[:50] for a in anthropic_selected])
        else:
            logger.warning("Anthropic関連記事が見つかりませんでした。一般記事で補填します。")

        # 2. 残り枠を一般記事で埋める
        remaining = self.select_count - len(selected)
        selected.extend(general_articles[:remaining])

        # 3. Anthropic記事が見つからず枠が余った場合、スコア上位で補填
        if len(selected) < self.select_count:
            already_urls = {a.get("url", "") for a in selected}
            for a in scored:
                if len(selected) >= self.select_count:
                    break
                if a.get("url", "") not in already_urls:
                    selected.append(a)

        logger.info("選定: %d 記事 (Anthropic枠: %d)", len(selected), len(anthropic_selected))
        return selected
