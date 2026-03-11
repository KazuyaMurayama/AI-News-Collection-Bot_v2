"""IMAP経由リアクションメール処理モジュール"""

import email
import imaplib
import logging
import os
import re
from email.header import decode_header

logger = logging.getLogger(__name__)

REACTION_PATTERN = re.compile(
    r"\[AI-NEWS-REACT\]\s+(\d{4}-\d{2}-\d{2})\s*/\s*(?:Story|記事)\s+(\d+)\s*/\s*(\w+)"
)

REACTION_RATINGS = {
    "excellent": 5,
    "good": 4,
    "read_later": 3,
    "so_so": 2,
}


def _decode_subject(msg: email.message.Message) -> str:
    """メールの件名をデコードする。"""
    subject = msg.get("Subject", "")
    decoded_parts = decode_header(subject)
    parts: list[str] = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(str(part))
    return " ".join(parts)


class EmailReactionProcessor:
    """IMAP経由でリアクションメールを処理する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        gmail_config = config.get("delivery", {}).get("gmail", {})
        self.email_addr = gmail_config.get("sender", "")

    def process(self) -> list[dict]:
        """未読のリアクションメールを処理する。"""
        password = os.environ.get("GMAIL_APP_PASSWORD", "")
        if not password or not self.email_addr:
            logger.warning("IMAP認証情報が不足")
            return []

        reactions: list[dict] = []

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_addr, password)
            mail.select("INBOX")

            _, data = mail.search(None, '(UNSEEN SUBJECT "[AI-NEWS-REACT]")')
            if not data[0]:
                logger.info("未処理のリアクションメールなし")
                mail.logout()
                return []

            msg_ids = data[0].split()
            logger.info("リアクションメール %d 件を処理", len(msg_ids))

            for msg_id in msg_ids:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0]
                if isinstance(raw, tuple):
                    raw = raw[1]
                msg = email.message_from_bytes(raw)
                subject = _decode_subject(msg)
                match = REACTION_PATTERN.search(subject)

                if match:
                    date_str = match.group(1)
                    story_id = int(match.group(2))
                    reaction_type = match.group(3).lower()
                    rating = REACTION_RATINGS.get(reaction_type, 0)

                    reactions.append({
                        "date": date_str,
                        "story_id": story_id,
                        "reaction_type": reaction_type,
                        "rating": rating,
                    })
                    logger.info(
                        "リアクション: %s / 記事 %d / %s (rating=%d)",
                        date_str, story_id, reaction_type, rating,
                    )

                # 既読マーク
                mail.store(msg_id, "+FLAGS", "\\Seen")

            mail.logout()

        except Exception as e:
            logger.error("IMAP処理エラー: %s", e)

        return reactions
