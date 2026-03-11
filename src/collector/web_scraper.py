"""Webスクレイピング収集モジュール"""

import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "AI-News-Bot/1.0"
REQUEST_INTERVAL = 2  # 秒


def _check_robots_txt(url: str) -> bool:
    """robots.txtを確認してクロール可否を判定する。"""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


class WebScraper:
    """CSSセレクタベースのWebスクレイピングコレクター。"""

    def __init__(self) -> None:
        self._last_request_time: float = 0

    def _wait(self) -> None:
        """リクエスト間隔を守る。"""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)

    def collect(
        self,
        source: dict,
        article_selector: str = "article",
        title_selector: str = "h2 a",
        summary_selector: str = "p",
    ) -> list[dict]:
        """指定URLからCSSセレクタで記事を抽出する。"""
        url = source["url"]

        if not _check_robots_txt(url):
            logger.warning("robots.txt によりアクセス不可: %s", url)
            return []

        self._wait()
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        self._last_request_time = time.time()
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        articles: list[dict] = []

        for item in soup.select(article_selector):
            title_el = item.select_one(title_selector)
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                parsed = urlparse(url)
                link = f"{parsed.scheme}://{parsed.netloc}{link}"

            summary_el = item.select_one(summary_selector)
            summary = summary_el.get_text(strip=True)[:1500] if summary_el else ""

            if title and link:
                articles.append(
                    {
                        "title": title,
                        "url": link,
                        "summary": summary,
                        "published": "",
                        "source": source.get("name", "Web"),
                        "category": source.get("category", ""),
                        "language": source.get("language", "en"),
                    }
                )

        return articles
