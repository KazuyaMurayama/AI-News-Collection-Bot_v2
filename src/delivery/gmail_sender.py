"""Gmail SMTP/OAuth2 送信モジュール"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..utils.retry import with_retry

logger = logging.getLogger(__name__)


class GmailSender:
    """Gmail経由でメールを送信する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        gmail_config = config.get("delivery", {}).get("gmail", {})
        self.auth_method = gmail_config.get("auth_method", "smtp")
        self.sender = gmail_config.get("sender", "")
        self.recipients = gmail_config.get("recipients", [])
        smtp_config = gmail_config.get("smtp", {})
        self.smtp_host = smtp_config.get("host", "smtp.gmail.com")
        self.smtp_port = smtp_config.get("port", 587)
        self.use_tls = smtp_config.get("use_tls", True)

    def authenticate(self) -> bool:
        """認証情報の検証。"""
        if self.auth_method == "smtp":
            password = os.environ.get("GMAIL_APP_PASSWORD", "")
            if not password:
                logger.error("GMAIL_APP_PASSWORD が未設定")
                return False
            return True
        elif self.auth_method == "oauth2":
            return self._authenticate_oauth2()
        else:
            logger.error("未対応の認証方式: %s", self.auth_method)
            return False

    def _authenticate_oauth2(self) -> bool:
        """OAuth2認証。"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow

            token_path = os.environ.get("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json")
            creds_path = os.environ.get("GMAIL_CREDENTIALS_PATH", "./credentials/gmail_credentials.json")
            scopes = ["https://www.googleapis.com/auth/gmail.send"]

            creds = None
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
                    creds = flow.run_local_server(port=0)
                with open(token_path, "w") as f:
                    f.write(creds.to_json())

            self._oauth2_creds = creds
            return True
        except Exception as e:
            logger.error("OAuth2認証失敗: %s", e)
            return False

    @with_retry(max_attempts=3, backoff_base=2, retry_on=(smtplib.SMTPException, ConnectionError, OSError))
    def send_email(
        self,
        subject: str,
        html_body: str,
        plain_body: str,
        recipients: list[str] | None = None,
    ) -> bool:
        """メールを送信する。"""
        to_addrs = recipients or self.recipients
        if not to_addrs:
            logger.error("送信先が未設定")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self.sender
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if self.auth_method == "smtp":
            return self._send_smtp(msg, to_addrs)
        elif self.auth_method == "oauth2":
            return self._send_oauth2(msg, to_addrs)
        return False

    def _send_smtp(self, msg: MIMEMultipart, to_addrs: list[str]) -> bool:
        """SMTP経由で送信する。"""
        password = os.environ.get("GMAIL_APP_PASSWORD", "")
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.sender, password)
            server.sendmail(self.sender, to_addrs, msg.as_string())
        logger.info("メール送信成功 (SMTP): %s", to_addrs)
        return True

    def _send_oauth2(self, msg: MIMEMultipart, to_addrs: list[str]) -> bool:
        """OAuth2経由で送信する。"""
        try:
            import base64

            from googleapiclient.discovery import build

            service = build("gmail", "v1", credentials=self._oauth2_creds)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            logger.info("メール送信成功 (OAuth2): %s", to_addrs)
            return True
        except Exception as e:
            logger.error("OAuth2送信失敗: %s", e)
            return False

    def send_daily_digest(
        self,
        date_str: str,
        headline: str,
        html_body: str,
        plain_body: str,
    ) -> bool:
        """日次ダイジェストメールを送信する。"""
        subject_template = (
            self.config.get("delivery", {})
            .get("gmail", {})
            .get("subject_template", "[AIニュース] {date} - {headline} 他")
        )
        subject = subject_template.format(date=date_str, headline=headline)
        return self.send_email(subject, html_body, plain_body)

    def send_error_report(self, error_msg: str) -> bool:
        """エラーレポートメールを送信する。"""
        subject = "[AIニュース] エラーレポート"
        html = f"<html><body><h2>エラーレポート</h2><pre>{error_msg}</pre></body></html>"
        return self.send_email(subject, html, error_msg)
