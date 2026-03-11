"""FastAPIリアクションサーバー"""

import logging
from pathlib import Path

import frontmatter
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from .updater import FrontmatterUpdater

logger = logging.getLogger(__name__)

_config: dict = {}


def create_app(config: dict | None = None) -> FastAPI:
    """FastAPIアプリケーションを作成する。"""
    global _config
    if config:
        _config = config

    app = FastAPI(title="AI News Bot Reaction Server", version="2.0.0")

    kb_config = _config.get("knowledge_base", {})
    daily_dir = Path(kb_config.get("daily_dir", "./knowledge_base/daily"))

    @app.get("/health")
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "2.0.0"}

    @app.get("/stats")
    @app.get("/api/stats")
    async def stats():
        md_files = list(daily_dir.glob("*_ai_news.md"))
        total_stories = 0
        total_reactions = 0
        for f in md_files:
            try:
                post = frontmatter.load(str(f))
                total_stories += post.metadata.get("num_stories", 0)
                total_reactions += post.metadata.get("total_reactions", 0)
            except Exception:
                pass
        return {
            "total_days": len(md_files),
            "total_stories": total_stories,
            "total_reactions": total_reactions,
        }

    @app.get("/react", response_class=HTMLResponse)
    async def react(
        date: str = Query(...),
        story: int = Query(...),
        reaction: str = Query(...),
    ):
        updater = FrontmatterUpdater(_config)
        rating = {"excellent": 5, "good": 4, "read_later": 3, "so_so": 2}.get(reaction.lower(), 0)
        success = updater.update_reaction(date, story, reaction.lower(), rating)
        emoji = {"excellent": "⭐", "good": "👍", "so_so": "🤔", "read_later": "📌"}.get(reaction.lower(), "✅")
        status_msg = "ありがとうございます！評価を記録しました。" if success else "エラーが発生しました。"
        return f"""
        <html><head><meta charset="utf-8"><title>評価完了</title>
        <style>body{{font-family:sans-serif;text-align:center;padding:50px;background:#f5f5f5;}}
        .card{{background:white;padding:40px;border-radius:12px;max-width:400px;margin:auto;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}</style>
        </head><body><div class="card">
        <h1>{emoji}</h1><h2>{status_msg}</h2>
        <p>{date} / 記事 {story} / {reaction}</p>
        </div></body></html>
        """

    @app.get("/api/reaction/{date}/{story_id}/{reaction_type}")
    async def api_react(date: str, story_id: int, reaction_type: str):
        updater = FrontmatterUpdater(_config)
        rating = {"excellent": 5, "good": 4, "read_later": 3, "so_so": 2}.get(reaction_type.lower(), 0)
        success = updater.update_reaction(date, story_id, reaction_type.lower(), rating)
        return {"success": success, "date": date, "story_id": story_id, "reaction": reaction_type}

    @app.get("/api/stories/{date}")
    async def get_stories(date: str):
        md_path = daily_dir / f"{date}_ai_news.md"
        if not md_path.exists():
            return JSONResponse(status_code=404, content={"error": "not found"})
        post = frontmatter.load(str(md_path))
        return {
            "date": date,
            "stories": post.metadata.get("stories", []),
            "total_reactions": post.metadata.get("total_reactions", 0),
        }

    @app.get("/api/stories/{date}/{story_id}")
    async def get_story(date: str, story_id: int):
        md_path = daily_dir / f"{date}_ai_news.md"
        if not md_path.exists():
            return JSONResponse(status_code=404, content={"error": "not found"})
        post = frontmatter.load(str(md_path))
        stories = post.metadata.get("stories", [])
        idx = story_id - 1
        if 0 <= idx < len(stories):
            return {"date": date, "story_id": story_id, "story": stories[idx]}
        return JSONResponse(status_code=404, content={"error": "story not found"})

    @app.get("/api/search")
    async def search_articles(
        q: str = Query(default=""),
        tag: str = Query(default=""),
        min_rating: float = Query(default=0),
    ):
        from ..knowledge.search import search_fulltext, search_by_tag, filter_by_rating

        results = []
        if q:
            results = search_fulltext(q, str(daily_dir))
        elif tag:
            results = search_by_tag(tag, str(daily_dir))
        else:
            from ..knowledge.search import get_all_articles
            results = get_all_articles(str(daily_dir))

        if min_rating > 0:
            results = [r for r in results if r.get("rating", 0) >= min_rating]

        return {"results": results, "count": len(results)}

    @app.get("/api/summary/{year}/{month}")
    async def get_summary(year: int, month: int):
        monthly_dir = Path(kb_config.get("monthly_dir", "./knowledge_base/monthly"))
        md_path = monthly_dir / f"{year}-{month:02d}_summary.md"
        if not md_path.exists():
            return JSONResponse(status_code=404, content={"error": "not found"})
        post = frontmatter.load(str(md_path))
        return {"year": year, "month": month, "content": post.content, "metadata": post.metadata}

    return app
