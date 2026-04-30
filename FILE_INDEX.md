# FILE_INDEX.md — AI-News-Collection-Bot_v2

> **新セッション開始時に必ずこのファイルを読む。**
> ファイル追加・削除・移動時は必ずこのファイルを更新すること。
> 最終更新: 2026-04-30

## 概要
AIニュースを自動収集・要約・メール/LINE配信するボット v2。フィードバック学習・知識ベース管理・GitHub Actionsによる自動実行対応。

**スタック:** Python, GitHub Actions, HTML, Markdown

---

## 📋 最初に読むべきファイル

| 優先度 | ファイル | 内容 |
|---|---|---|
| ★★★ | `src/main.py` | メインエントリポイント |
| ★★★ | `config.yaml` | 設定ファイル（API Key等） |
| ★★★ | `.github/workflows/daily_news.yml` | 自動実行ワークフロー |
| ★★ | `requirements.txt` | Python依存関係 |
| ★★ | `src/delivery/gmail_sender.py` | Gmail送信モジュール |

---

## 🗂️ ディレクトリ構造

```
AI-News-Collection-Bot_v2/
├── config.yaml                  ← 設定ファイル
├── requirements.txt
├── setup.sh
├── .github/workflows/daily_news.yml ← 自動実行
├── scripts/
│   ├── install_cron.sh
│   └── install_task_scheduler.bat
├── knowledge_base/
│   ├── daily/
│   └── monthly/
└── src/
    ├── main.py                  ← エントリポイント
    ├── collector/
    │   ├── news_api.py
    │   ├── rss_collector.py
    │   ├── web_scraper.py
    │   └── selector.py
    ├── delivery/
    │   ├── gmail_sender.py
    │   ├── line_sender.py
    │   └── html_converter.py
    ├── writer/
    │   ├── storyteller.py
    │   ├── markdown_gen.py
    │   └── templates/
    ├── knowledge/
    │   ├── search.py
    │   ├── summarizer.py
    │   └── tagger.py
    ├── feedback/
    │   ├── api_server.py
    │   ├── email_processor.py
    │   └── updater.py
    └── utils/config.py logger.py retry.py
```

---

## 📑 全ファイル一覧

| パス | 種別 | 説明 |
|---|---|---|
| `src/main.py` | Python | メインエントリポイント |
| `src/collector/news_api.py` | Python | ニュースAPI収集 |
| `src/collector/rss_collector.py` | Python | RSSフィード収集 |
| `src/collector/web_scraper.py` | Python | Webスクレイピング |
| `src/collector/selector.py` | Python | 記事セレクター |
| `src/delivery/gmail_sender.py` | Python | Gmail送信 |
| `src/delivery/line_sender.py` | Python | LINE送信 |
| `src/delivery/html_converter.py` | Python | HTML変換 |
| `src/writer/storyteller.py` | Python | ストーリー形式ライター |
| `src/writer/markdown_gen.py` | Python | Markdown生成 |
| `src/knowledge/search.py` | Python | 知識ベース検索 |
| `src/feedback/api_server.py` | Python | フィードバックAPIサーバー |
| `config.yaml` | 設定 | システム設定（APIキー・配信先等） |
| `requirements.txt` | 設定 | Python依存関係 |
| `.github/workflows/daily_news.yml` | CI/CD | 日次自動実行ワークフロー |
| `knowledge_base/` | データ | 蓄積知識ベース（日次・月次） |

---

## 🔖 ファイル更新ルール

1. 新ファイル追加時: 該当セクションに1行追加
2. ファイル削除・移動時: 該当行を削除または更新
3. 更新後: `git add FILE_INDEX.md && git commit -m "docs: FILE_INDEX.md更新"`
