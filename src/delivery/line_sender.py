"""LINE Notify送信モジュール（オプション）"""

import logging
import os

import requests

from ..utils.retry import with_retry

logger = logging.getLogger(__name__)

LINE_NOTIFY_URL = "https://notify-api.line.me/api/notify"
MAX_MESSAGE_LENGTH = 1000


class LineSender:
    """LINE Notifyでテキスト通知を送信する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.enabled = config.get("delivery", {}).get("line", {}).get("enabled", False)

    @with_retry(max_attempts=3, backoff_base=2, retry_on=(requests.RequestException,))
    def send(self, message: str) -> bool:
        """LINE Notifyでメッセージを送信する。"""
        if not self.enabled:
            logger.info("LINE Notify は無効")
            return False

        token = os.environ.get("LINE_NOTIFY_TOKEN", "")
        if not token:
            logger.warning("LINE_NOTIFY_TOKEN が未設定")
            return False

        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[: MAX_MESSAGE_LENGTH - 3] + "..."

        resp = requests.post(
            LINE_NOTIFY_URL,
            headers={"Authorization": f"Bearer {token}"},
            data={"message": message},
            timeout=30,
        )
        resp.raise_for_status()
        logger.info("LINE Notify 送信成功")
        return True

    def send_daily_digest(self, date_str: str, stories: list[dict]) -> bool:
        """日次ダイジェストをLINE Notifyで送信する。"""
        parts: list[str] = [f"\n📰 AIニュース {date_str}"]

        for i, story in enumerate(stories):
            title = story.get("story_title", story.get("title", ""))
            source = story.get("source", "")
            url = story.get("url", "")
            summary = story.get("summary", "")[:100]
            parts.append(f"\n{i + 1}. {title}")
            parts.append(f"   [{source}] {summary}")
            parts.append(f"   {url}")

        message = "\n".join(parts)
        return self.send(message)
