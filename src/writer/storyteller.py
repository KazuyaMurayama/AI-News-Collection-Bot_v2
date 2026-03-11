"""Claude API日本語翻訳・解説記事生成モジュール"""

import logging
import os
import re

import anthropic

from ..utils.retry import with_retry

logger = logging.getLogger(__name__)

# フレームワーク選択用キーワード
FRAMEWORK_KEYWORDS = {
    "STAR": [
        "導入", "採用", "実装", "deploy", "case study", "企業", "ROI",
        "活用事例", "運用", "パートナー",
    ],
    "ヒーローズジャーニー": [
        "革新", "breakthrough", "新モデル", "論文", "リリース", "GPT", "LLM",
        "発表", "新技術", "open source", "オープンソース",
    ],
    "Before-After-Bridge": [
        "効率化", "自動化", "DX", "ワークフロー", "update", "改善",
        "アップデート", "性能向上", "高速化",
    ],
    "PAS": [
        "課題", "リスク", "セキュリティ", "規制", "バイアス", "脆弱性",
        "問題", "懸念", "プライバシー", "倫理",
    ],
}

FRAMEWORK_PROMPTS = {
    "STAR": "STARフレームワーク（状況→課題→行動→結果）で構成してください。",
    "ヒーローズジャーニー": "ヒーローズジャーニー（日常→冒険への誘い→試練→変容→帰還）で構成してください。",
    "Before-After-Bridge": "Before/After/Bridgeフレームワーク（以前→以後→その橋渡し）で構成してください。",
    "PAS": "PASフレームワーク（問題提起→問題の深掘り→解決策提示）で構成してください。",
}

SYSTEM_PROMPT = """あなたは日本のビジネスパーソン向けAIトレンド解説の一流テクノロジーライターです。

【最重要ルール】
- すべて日本語で出力してください。英語での出力は禁止です。
- ただし、固有名詞（GPT, Claude, Meta, Google等）や技術用語（LLM, API, RAG等）はそのまま使用して構いません。

【記事の構成要素（必須）】
1. フック: 読者の関心を引く導入（1-2文）
2. 背景・文脈: このニュースが生まれた背景
3. 技術詳細: 技術的なポイントをわかりやすく解説
4. 数字・データ: 具体的な数値やデータを含める
5. 業界インパクト: この技術・ニュースが業界に与える影響
6. 日本企業への示唆: 日本のビジネスパーソンが知るべきポイント
7. 今後の展望と課題: 将来の方向性とリスク
8. クロージング: まとめと読者へのメッセージ

【フォーマット】
- 2000-3000文字
- タイトルは日本語（疑問形 or 数字入り推奨）
- Markdown太字（**...**）を使用可
- 見出し（#）は使用しない
- 最初の行にタイトルを書く
"""


def _select_framework_by_keywords(title: str, summary: str) -> str | None:
    """キーワードベースでフレームワークを自動選択する。"""
    text = (title + " " + summary).lower()
    scores: dict[str, int] = {}
    for framework, keywords in FRAMEWORK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[framework] = score

    if scores:
        return max(scores, key=scores.get)  # type: ignore[arg-type]
    return None


@with_retry(max_attempts=2, backoff_base=2, retry_on=(Exception,))
def _select_framework_by_api(title: str, summary: str) -> str:
    """Claude APIでフレームワークを選択する。"""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        temperature=0.3,
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下のニュースに最適なストーリーテリングフレームワークを1つ選んでください。\n"
                    f"選択肢: STAR, ヒーローズジャーニー, Before-After-Bridge, PAS\n\n"
                    f"タイトル: {title}\n概要: {summary[:500]}\n\n"
                    f'JSON形式で回答: {{"framework": "...", "reason": "..."}}'
                ),
            }
        ],
    )
    import json

    content = response.content[0].text
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0] if "```json" in content else content.split("```")[1].split("```")[0]
    data = json.loads(content.strip())
    return data.get("framework", "ヒーローズジャーニー")


def select_framework(title: str, summary: str) -> str:
    """フレームワークを自動選択する（キーワード優先、API補完）。"""
    framework = _select_framework_by_keywords(title, summary)
    if framework:
        return framework

    try:
        return _select_framework_by_api(title, summary)
    except Exception as e:
        logger.warning("フレームワークAPI選択失敗: %s (デフォルト使用)", e)
        return "ヒーローズジャーニー"


def _contains_japanese(text: str, min_ratio: float = 0.1) -> bool:
    """テキストに十分な日本語が含まれているか検証する。"""
    if not text:
        return False
    japanese_chars = sum(
        1
        for c in text
        if (
            "\u3040" <= c <= "\u309F"  # ひらがな
            or "\u30A0" <= c <= "\u30FF"  # カタカナ
            or "\u4E00" <= c <= "\u9FFF"  # 漢字
        )
    )
    return (japanese_chars / len(text)) >= min_ratio


def extract_title_and_body(text: str) -> tuple[str, str]:
    """最初の非空行をタイトル、残りを本文として分離する。"""
    lines = text.strip().split("\n")
    title = ""
    body_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            title = stripped
            title = re.sub(r"^\*\*(.+)\*\*$", r"\1", title)
            title = re.sub(r"^#+\s*", "", title)
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    return title, body


class StoryTeller:
    """Claude APIで記事をストーリーに変換する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.claude_config = config.get("claude", {})

    @with_retry(max_attempts=2, backoff_base=2, retry_on=(Exception,))
    def _generate(self, article: dict, framework: str) -> str:
        """Claude APIでストーリーを生成する。"""
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

        framework_instruction = FRAMEWORK_PROMPTS.get(framework, "")

        user_prompt = (
            f"以下のニュース記事を、日本のビジネスパーソン向けの2000-3000文字の日本語解説記事に変換してください。\n\n"
            f"【フレームワーク】{framework_instruction}\n\n"
            f"【元記事情報】\n"
            f"タイトル: {article['title']}\n"
            f"ソース: {article.get('source', 'N/A')}\n"
            f"概要: {article.get('summary', 'N/A')}\n"
            f"公開日: {article.get('published', 'N/A')}\n\n"
            f"日本語タイトル（疑問形 or 数字入り）を最初の行に書き、"
            f"続けて本文を書いてください。"
        )

        response = client.messages.create(
            model=self.claude_config.get("model", "claude-sonnet-4-20250514"),
            max_tokens=self.claude_config.get("max_tokens", 8192),
            temperature=self.claude_config.get("temperature", 0.7),
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return response.content[0].text

    def transform(self, article: dict) -> dict:
        """記事をストーリーに変換する。"""
        framework = select_framework(
            article.get("title", ""), article.get("summary", "")
        )
        logger.info("フレームワーク: %s - %s", framework, article.get("title", "")[:50])

        try:
            story_text = self._generate(article, framework)
        except Exception as e:
            logger.error("ストーリー生成失敗: %s", e)
            return {
                **article,
                "story_title": f"【要確認】{article.get('title', '')}",
                "story_body": article.get("summary", ""),
                "framework": framework,
            }

        if not _contains_japanese(story_text):
            logger.warning("日本語チェック不合格、再試行")
            try:
                retry_prompt_article = {
                    **article,
                    "summary": (
                        article.get("summary", "")
                        + "\n\n【注意】前回の出力が英語でした。必ず日本語で出力してください。"
                    ),
                }
                story_text = self._generate(retry_prompt_article, framework)
            except Exception:
                pass

        title, body = extract_title_and_body(story_text)

        return {
            **article,
            "story_title": title or f"【要確認】{article.get('title', '')}",
            "story_body": body or story_text,
            "framework": framework,
        }


def transform_to_story(article: dict, config: dict) -> dict:
    """ユーティリティ関数: 記事をストーリーに変換する。"""
    teller = StoryTeller(config)
    return teller.transform(article)


@with_retry(max_attempts=2, backoff_base=2, retry_on=(Exception,))
def generate_insight(stories: list[dict], config: dict) -> str:
    """記事群の共通テーマを分析し、インサイトを生成する。"""
    claude_config = config.get("claude", {})
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    stories_text = ""
    for i, s in enumerate(stories):
        stories_text += (
            f"\n--- 記事 {i + 1} ---\n"
            f"タイトル: {s.get('story_title', s.get('title', ''))}\n"
            f"本文冒頭: {s.get('story_body', s.get('summary', ''))[:300]}\n"
        )

    response = client.messages.create(
        model=claude_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=2048,
        temperature=claude_config.get("temperature", 0.7),
        system=(
            "あなたはAI業界の動向を分析する専門家です。すべて日本語で出力してください。"
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下の本日のAIニュース記事群を分析し、800-1200文字の「本日のインサイト」を生成してください。\n\n"
                    f"【必須要素】\n"
                    f"1. 共通テーマ: 記事群に共通するテーマ\n"
                    f"2. マクロトレンド: AI業界全体の動向\n"
                    f"3. 日本市場の機会と課題\n"
                    f"4. アクションポイント: 5つ以上の具体的アクション\n"
                    f"5. 今後1-3ヶ月の注目点\n\n"
                    f"記事一覧:\n{stories_text}"
                ),
            }
        ],
    )

    return response.content[0].text
