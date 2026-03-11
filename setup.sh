#!/bin/bash
# AI News Collection Bot v2 - セットアップスクリプト

set -e

echo "=== AI News Collection Bot v2 セットアップ ==="

# Python バージョンチェック
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "エラー: Python 3.11以上が必要です (現在: $PYTHON_VERSION)"
    exit 1
fi
echo "Python $PYTHON_VERSION を検出"

# 仮想環境作成
if [ ! -d "venv" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
fi

echo "仮想環境をアクティベート"
source venv/bin/activate

# 依存パッケージインストール
echo "依存パッケージをインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# ディレクトリ作成
echo "ディレクトリを作成中..."
mkdir -p knowledge_base/daily knowledge_base/monthly logs credentials

# .env ファイル
if [ ! -f ".env" ]; then
    echo ".env ファイルを作成中..."
    cp .env.example .env
    echo "⚠️  .env ファイルを編集してAPIキーを設定してください"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. .env ファイルを編集してAPIキーを設定"
echo "2. python -m src.main --dry-run でテスト実行"
echo "3. python -m src.main で本番実行"
echo "4. python -m src.main --server でリアクションサーバー起動"
