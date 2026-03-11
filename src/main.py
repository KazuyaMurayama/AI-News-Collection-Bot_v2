"""メインオーケストレーター（CLIエントリーポイント）

python -m src.main で実行。

CLI引数:
  --date YYYY-MM-DD   実行対象日付（デフォルト: 今日JST）
  --dry-run           配信せずMarkdown生成まで
  --server            リアクションFastAPIサーバー起動
  --process-reactions  リアクションメール処理のみ実行
"""

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .utils.config import AppConfig, validate_config, validate_env
from .utils.logger import setup_logger


def get_today_jst() -> str:
    """日本時間の今日の日付を返す。"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y-%m-%d")


def run_server(config: dict) -> None:
    """FastAPIリアクションサーバーを起動する。"""
    import uvicorn
    from .feedback.api_server import create_app

    app = create_app(config)
    server_config = config.get("feedback_server", {})
    uvicorn.run(
        app,
        host=server_config.get("host", "127.0.0.1"),
        port=server_config.get("port", 8321),
    )


def run_process_reactions(config: dict, logger) -> None:
    """リアクションメール処理のみ実行する。"""
    from .feedback.email_processor import EmailReactionProcessor
    from .feedback.updater import FrontmatterUpdater

    processor = EmailReactionProcessor(config)
    updater = FrontmatterUpdater(config)

    reactions = processor.process()
    for r in reactions:
        updater.update_reaction(
            r["date"], r["story_id"], r["reaction_type"], r["rating"]
        )
    logger.info("リアクション処理完了: %d 件", len(reactions))


def run_pipeline(config: dict, date_str: str, dry_run: bool, logger) -> None:
    """メインパイプライン10ステップを実行する。"""
    from .collector import collect_all
    from .writer.storyteller import StoryTeller, generate_insight
    from .writer.markdown_gen import MarkdownGenerator
    from .knowledge.tagger import AutoTagger
    from .delivery.gmail_sender import GmailSender
    from .delivery.html_converter import HTMLConverter
    from .delivery.line_sender import LineSender
    from .feedback.email_processor import EmailReactionProcessor
    from .feedback.updater import FrontmatterUpdater

    kb_config = config.get("knowledge_base", {})
    daily_dir = Path(kb_config.get("daily_dir", "./knowledge_base/daily"))
    daily_dir.mkdir(parents=True, exist_ok=True)

    # Step 1.5: リアクションメール処理
    logger.info("=== Step 1.5: リアクションメール処理 ===")
    try:
        processor = EmailReactionProcessor(config)
        updater = FrontmatterUpdater(config)
        reactions = processor.process()
        for r in reactions:
            updater.update_reaction(
                r["date"], r["story_id"], r["reaction_type"], r["rating"]
            )
        logger.info("リアクション処理: %d 件", len(reactions))
    except Exception as e:
        logger.warning("リアクション処理エラー (続行): %s", e)

    # Step 2: ニュース収集
    logger.info("=== Step 2: ニュース収集 ===")
    selected = collect_all(config)

    # フォールバック: 記事0件
    if not selected:
        logger.warning("記事0件 - フォールバック記事を生成")
        selected = [
            {
                "title": "本日のAIニュースは取得できませんでした",
                "url": "",
                "summary": "ニュースソースからの記事取得に失敗しました。明日の配信をお待ちください。",
                "published": datetime.now(timezone.utc).isoformat(),
                "source": "System",
                "category": "お知らせ",
                "language": "ja",
            }
        ]

    logger.info("選定記事: %d 件", len(selected))

    # Step 3: 中間JSON保存
    logger.info("=== Step 3: 中間JSON保存 ===")
    candidates_path = daily_dir / f"{date_str}_candidates.json"
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2, default=str)
    logger.info("中間JSON保存: %s", candidates_path)

    # Step 4: ストーリーテリング変換
    logger.info("=== Step 4: ストーリーテリング変換 ===")
    storyteller = StoryTeller(config)
    stories: list[dict] = []
    for article in selected:
        try:
            story = storyteller.transform(article)
            stories.append(story)
        except Exception as e:
            logger.error("ストーリー変換失敗: %s", e)
            stories.append({
                **article,
                "story_title": f"【要確認】{article.get('title', '')}",
                "story_body": article.get("summary", ""),
                "framework": "",
            })

    # Step 5: 自動タグ付け
    logger.info("=== Step 5: 自動タグ付け ===")
    try:
        tagger = AutoTagger(config)
        stories = tagger.tag_stories(stories)
    except Exception as e:
        logger.warning("タグ付けエラー (続行): %s", e)

    # Step 6: インサイト生成
    logger.info("=== Step 6: インサイト生成 ===")
    insight = ""
    try:
        insight = generate_insight(stories, config)
        logger.info("インサイト生成完了 (%d文字)", len(insight))
    except Exception as e:
        logger.warning("インサイト生成エラー (続行): %s", e)

    # Step 7: Markdown生成・保存
    logger.info("=== Step 7: Markdown生成・保存 ===")
    md_gen = MarkdownGenerator(config)
    md_path = md_gen.generate(date_str, stories, insight)
    logger.info("Markdown保存: %s", md_path)

    if dry_run:
        logger.info("=== Dry-run モード: 配信をスキップ ===")
        return

    # Step 8: Gmail配信
    logger.info("=== Step 8: Gmail配信 ===")
    gmail_config = config.get("delivery", {}).get("gmail", {})
    if gmail_config.get("enabled", True):
        try:
            converter = HTMLConverter(config)
            html_body = converter.convert(date_str, stories, insight)
            plain_body = converter.convert_to_plain_text(date_str, stories, insight)

            sender = GmailSender(config)
            if sender.authenticate():
                headline = stories[0].get("story_title", stories[0].get("title", ""))
                sender.send_daily_digest(date_str, headline, html_body, plain_body)
                logger.info("Gmail配信完了")
            else:
                logger.error("Gmail認証失敗")
        except Exception as e:
            logger.error("Gmail配信エラー: %s", e)

    # Step 9: LINE配信（オプション）
    logger.info("=== Step 9: LINE配信 ===")
    line_config = config.get("delivery", {}).get("line", {})
    if line_config.get("enabled", False):
        try:
            line_sender = LineSender(config)
            line_sender.send_daily_digest(date_str, stories)
            logger.info("LINE配信完了")
        except Exception as e:
            logger.warning("LINE配信エラー: %s", e)

    logger.info("=== パイプライン完了 ===")


def main() -> None:
    """CLIエントリーポイント。"""
    parser = argparse.ArgumentParser(description="AI News Collection Bot v2")
    parser.add_argument("--date", type=str, default=None, help="実行対象日付 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="配信せずMarkdown生成まで")
    parser.add_argument("--server", action="store_true", help="リアクションFastAPIサーバー起動")
    parser.add_argument("--process-reactions", action="store_true", help="リアクションメール処理のみ")
    args = parser.parse_args()

    # Step 1: ログ初期化・設定読み込み
    app_config = AppConfig.get_instance()
    config = app_config.config

    log_config = config.get("logging", {})
    logger = setup_logger(
        "ai_news_bot",
        log_dir=log_config.get("dir", "./logs/"),
        log_file=log_config.get("app_log", "app.log"),
        level=log_config.get("level", "INFO"),
        log_format=log_config.get("format", "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"),
    )

    logger.info("AI News Bot v2.0 起動")

    # 設定バリデーション
    config_errors = validate_config(config)
    if config_errors:
        for err in config_errors:
            logger.error("設定エラー: %s", err)
        sys.exit(1)

    env_errors = validate_env()
    if env_errors:
        for err in env_errors:
            logger.warning("環境変数: %s", err)

    date_str = args.date or get_today_jst()

    if args.server:
        run_server(config)
        return

    if args.process_reactions:
        run_process_reactions(config, logger)
        return

    try:
        run_pipeline(config, date_str, args.dry_run, logger)
    except Exception as e:
        logger.error("致命的エラー: %s\n%s", e, traceback.format_exc())
        # Step 10: エラー通知
        try:
            from .delivery.gmail_sender import GmailSender

            sender = GmailSender(config)
            if sender.authenticate():
                sender.send_error_report(
                    f"日付: {date_str}\nエラー: {e}\n\n{traceback.format_exc()}"
                )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
