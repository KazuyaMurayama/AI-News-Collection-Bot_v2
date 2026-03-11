from .rss_collector import RSSCollector
from .news_api import NewsAPICollector, HackerNewsCollector
from .web_scraper import WebScraper
from .selector import ArticleSelector


def collect_all(config: dict, target_date: str | None = None) -> list[dict]:
    """全ソースからニュースを収集し、上位記事を選定して返す。"""
    candidates = collect_candidates(config, target_date)
    selector = ArticleSelector(config)
    selected = selector.select(candidates)
    return selected


def collect_candidates(config: dict, target_date: str | None = None) -> list[dict]:
    """全ソースから候補記事を収集する。"""
    import logging

    logger = logging.getLogger(__name__)
    all_articles: list[dict] = []

    sources = config.get("collection", {}).get("sources", [])

    for source in sources:
        if not source.get("enabled", True):
            continue
        try:
            source_type = source.get("type", "")
            if source_type == "rss":
                collector = RSSCollector()
                articles = collector.collect(source)
            elif source_type == "api":
                name = source.get("name", "")
                if "hacker" in name.lower():
                    collector = HackerNewsCollector()
                elif "newsapi" in name.lower():
                    collector = NewsAPICollector()
                else:
                    continue
                articles = collector.collect(source)
            else:
                continue
            all_articles.extend(articles)
            logger.info("%s: %d 記事を収集", source["name"], len(articles))
        except Exception as e:
            logger.warning("%s の収集に失敗 (他ソースで継続): %s", source.get("name", "?"), e)
            continue

    return all_articles
