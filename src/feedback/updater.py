"""Markdown Frontmatter更新モジュール"""

import logging
import threading
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)

_file_lock = threading.Lock()


class FrontmatterUpdater:
    """ナレッジベースのMarkdown Frontmatterを更新する。"""

    def __init__(self, config: dict) -> None:
        self.config = config
        kb_config = config.get("knowledge_base", {})
        self.daily_dir = Path(kb_config.get("daily_dir", "./knowledge_base/daily"))

    def _get_md_path(self, date_str: str) -> Path:
        return self.daily_dir / f"{date_str}_ai_news.md"

    def update_reaction(
        self,
        date_str: str,
        story_id: int,
        reaction_type: str,
        rating: int,
    ) -> bool:
        """リアクションをFrontmatterに反映する。"""
        md_path = self._get_md_path(date_str)
        if not md_path.exists():
            logger.warning("ファイルが見つかりません: %s", md_path)
            return False

        with _file_lock:
            try:
                post = frontmatter.load(str(md_path))
                stories = post.metadata.get("stories", [])

                story_idx = story_id - 1
                if 0 <= story_idx < len(stories):
                    story = stories[story_idx]
                    reactions = story.get("reactions", {})
                    reactions[reaction_type] = reactions.get(reaction_type, 0) + 1
                    story["reactions"] = reactions

                    total = sum(reactions.values())
                    if total > 0:
                        weighted = sum(
                            count * {"excellent": 5, "good": 4, "read_later": 3, "so_so": 2}.get(rt, 0)
                            for rt, count in reactions.items()
                        )
                        story["rating"] = round(weighted / total, 1)

                    stories[story_idx] = story
                    post.metadata["stories"] = stories

                    total_reactions = post.metadata.get("total_reactions", 0) + 1
                    post.metadata["total_reactions"] = total_reactions

                    md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
                    logger.info("Frontmatter更新: %s / 記事 %d / %s", date_str, story_id, reaction_type)
                    return True
                else:
                    logger.warning("記事ID %d は範囲外 (全%d件)", story_id, len(stories))
                    return False

            except Exception as e:
                logger.error("Frontmatter更新エラー: %s", e)
                return False
