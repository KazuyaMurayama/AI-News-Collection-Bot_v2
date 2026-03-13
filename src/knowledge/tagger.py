"""Claude API自動タグ付けモジュール"""

import json
import logging
import os

import anthropic

from ..utils.retry import with_retry

logger = logging.getLogger(__name__)

CATEGORY_TAGS = [
    "Anthropic AIエージェント",
    "業務効率化", "創造支援", "コスト削減", "新規事業", "研究・学術",
    "ヘルスケア", "教育", "金融", "製造", "マーケティング",
]

TECH_TAGS = [
    "LLM", "画像生成", "音声AI", "マルチモーダル", "RAG", "Agent",
    "ファインチューニング", "プロンプトエンジニアリング", "自然言語処理",
    "コンピュータビジョン", "強化学習", "ロボティクス", "エッジAI",
    "AutoML", "データセット",
]


class AutoTagger:
    """Claude APIで記事に自動タグ付けする。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.claude_config = config.get("claude", {})

    @with_retry(max_attempts=2, backoff_base=2, retry_on=(Exception,))
    def tag(self, story: dict) -> list[str]:
        """記事にタグを付与する。"""
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

        title = story.get("story_title", story.get("title", ""))
        body = story.get("story_body", story.get("summary", ""))[:1000]

        prompt = (
            f"以下のAIニュース記事に適切なタグを付けてください。\n\n"
            f"タイトル: {title}\n本文: {body}\n\n"
            f"【カテゴリタグ（1-3個選択）】\n{', '.join(CATEGORY_TAGS)}\n\n"
            f"【技術タグ（0-5個選択）】\n{', '.join(TECH_TAGS)}\n\n"
            f'JSON形式で回答: {{"category_tags": [...], "tech_tags": [...]}}'
        )

        response = client.messages.create(
            model=self.claude_config.get("model", "claude-sonnet-4-20250514"),
            max_tokens=512,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        if "```" in content:
            content = content.split("```json")[-1].split("```")[0] if "```json" in content else content.split("```")[1].split("```")[0]
        data = json.loads(content.strip())

        tags: list[str] = []
        for t in data.get("category_tags", []):
            if t in CATEGORY_TAGS:
                tags.append(t)
        for t in data.get("tech_tags", []):
            if t in TECH_TAGS:
                tags.append(t)

        return tags

    def tag_stories(self, stories: list[dict]) -> list[dict]:
        """複数記事にタグを付与する。"""
        for story in stories:
            try:
                tags = self.tag(story)
                story["tags"] = tags
                logger.info("タグ付与: %s → %s", story.get("story_title", "")[:30], tags)
            except Exception as e:
                logger.warning("タグ付与失敗: %s", e)
                story["tags"] = []
        return stories
