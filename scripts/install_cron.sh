#!/bin/bash
# Linux cron 設定スクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

CRON_SCHEDULE="0 6 * * *"  # 毎朝6:00 JST

CRON_CMD="cd $PROJECT_DIR && source venv/bin/activate && python -m src.main >> logs/cron.log 2>&1"

# 既存のcronエントリを確認
if crontab -l 2>/dev/null | grep -q "ai-news-bot"; then
    echo "既存のcronエントリを更新します"
    crontab -l | grep -v "ai-news-bot" | crontab -
fi

# cronエントリ追加
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_CMD  # ai-news-bot") | crontab -

echo "cronジョブを設定しました:"
echo "  スケジュール: $CRON_SCHEDULE"
echo "  コマンド: $CRON_CMD"
echo ""
echo "確認: crontab -l"
