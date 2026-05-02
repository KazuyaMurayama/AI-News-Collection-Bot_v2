# FILE_INDEX — AI-News-Collection-Bot_v2

> ⚠️ このファイルは自動生成です。手動編集は次回更新で上書きされます。

| 項目 | 値 |
|---|---|
| リポジトリ | KazuyaMurayama/AI-News-Collection-Bot_v2 |
| ブランチ | main |
| 総ファイル数 | 53 |
| 最終更新 | 2026-05-02 |
| 管理者 | 男座員也（Kazuya Oza） |

---

## カテゴリ別サマリー

| カテゴリ | ファイル数 |
|---|---|
| Documentation | 6 |
| Code | 36 |
| Data | 2 |
| Config | 3 |
| Other | 6 |

---

## ディレクトリ構成

```
.
├── .github/
│   └── workflows/
│       └── daily_news.yml
├── knowledge_base/
│   ├── daily/
│   │   └── .gitkeep
│   └── monthly/
│       └── .gitkeep
├── logs/
│   └── .gitkeep
├── scripts/
│   ├── install_cron.sh
│   ├── install_task_scheduler.bat
│   ├── run_daily.bat
│   └── run_once.sh
├── src/
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── news_api.py
│   │   ├── rss_collector.py
│   │   ├── selector.py
│   │   └── web_scraper.py
│   ├── delivery/
│   │   ├── __init__.py
│   │   ├── gmail_sender.py
│   │   ├── html_converter.py
│   │   └── line_sender.py
│   ├── feedback/
│   │   ├── __init__.py
│   │   ├── api_server.py
│   │   ├── email_processor.py
│   │   └── updater.py
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── summarizer.py
│   │   └── tagger.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── retry.py
│   ├── writer/
│   │   ├── templates/
│   │   │   ├── daily_template.md
│   │   │   └── email_template.html
│   │   ├── __init__.py
│   │   ├── markdown_gen.py
│   │   └── storyteller.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_collector.py
│   ├── test_delivery.py
│   ├── test_feedback.py
│   ├── test_integration.py
│   ├── test_utils.py
│   └── test_writer.py
├── .env.example
├── .gitignore
├── CLAUDE.md
├── config.yaml
├── FILE_INDEX.md
├── README.md
├── requirements.txt
├── setup.sh
├── tasks.md
└── Timeout_Prevention.md
```

---

## ファイル詳細

### Documentation (6件)

| ファイル | サイズ | 説明 |
|---|---|---|
| `CLAUDE.md` | 1.3 KB | Claude Code プロジェクト設定・命名ルール |
| `FILE_INDEX.md` | 3.5 KB | （このファイル）全ファイルインデックス |
| `README.md` | 2.2 KB | リポジトリ概要・セットアップ手順 |
| `src/writer/templates/daily_template.md` | 415 B | Markdown ドキュメント |
| `tasks.md` | 1.2 KB | タスク管理・セッション履歴 |
| `Timeout_Prevention.md` | 4.9 KB | タイムアウト対策ガイド |

### Code (36件)

| ファイル | サイズ | 説明 |
|---|---|---|
| `scripts/install_cron.sh` | 745 B | シェルスクリプト |
| `scripts/run_once.sh` | 267 B | シェルスクリプト |
| `setup.sh` | 1.5 KB | シェルスクリプト |
| `src/__init__.py` | - | Python スクリプト |
| `src/collector/__init__.py` | 1.8 KB | Python スクリプト |
| `src/collector/news_api.py` | 3.5 KB | Python スクリプト |
| `src/collector/rss_collector.py` | 2.6 KB | Python スクリプト |
| `src/collector/selector.py` | 10.6 KB | Python スクリプト |
| `src/collector/web_scraper.py` | 2.8 KB | Python スクリプト |
| `src/delivery/__init__.py` | 116 B | Python スクリプト |
| `src/delivery/gmail_sender.py` | 5.6 KB | Python スクリプト |
| `src/delivery/html_converter.py` | 2.9 KB | Python スクリプト |
| `src/delivery/line_sender.py` | 2.0 KB | Python スクリプト |
| `src/feedback/__init__.py` | 127 B | Python スクリプト |
| `src/feedback/api_server.py` | 5.3 KB | Python スクリプト |
| `src/feedback/email_processor.py` | 3.3 KB | Python スクリプト |
| `src/feedback/updater.py` | 2.6 KB | Python スクリプト |
| `src/knowledge/__init__.py` | 160 B | Python スクリプト |
| `src/knowledge/search.py` | 2.6 KB | Python スクリプト |
| `src/knowledge/summarizer.py` | 4.4 KB | Python スクリプト |
| `src/knowledge/tagger.py` | 3.0 KB | Python スクリプト |
| `src/main.py` | 9.3 KB | Python スクリプト |
| `src/utils/__init__.py` | 116 B | Python スクリプト |
| `src/utils/config.py` | 3.4 KB | Python スクリプト |
| `src/utils/logger.py` | 1.2 KB | Python スクリプト |
| `src/utils/retry.py` | 1.7 KB | Python スクリプト |
| `src/writer/__init__.py` | 119 B | Python スクリプト |
| `src/writer/markdown_gen.py` | 3.0 KB | Python スクリプト |
| `src/writer/storyteller.py` | 11.1 KB | Python スクリプト |
| `tests/__init__.py` | - | Python スクリプト |
| `tests/test_collector.py` | 5.8 KB | Python スクリプト |
| `tests/test_delivery.py` | 3.1 KB | Python スクリプト |
| `tests/test_feedback.py` | 3.0 KB | Python スクリプト |
| `tests/test_integration.py` | 3.9 KB | Python スクリプト |
| `tests/test_utils.py` | 3.9 KB | Python スクリプト |
| `tests/test_writer.py` | 3.5 KB | Python スクリプト |

### Data (2件)

| ファイル | サイズ | 説明 |
|---|---|---|
| `.github/workflows/daily_news.yml` | 1.2 KB | GitHub Actions ワークフロー |
| `config.yaml` | 4.6 KB | YAML 設定 |

### Config (3件)

| ファイル | サイズ | 説明 |
|---|---|---|
| `.env.example` | 296 B | 環境変数テンプレート |
| `.gitignore` | 324 B | Git 除外設定 |
| `requirements.txt` | 494 B | Python 依存パッケージリスト |

### Other (6件)

| ファイル | サイズ | 説明 |
|---|---|---|
| `knowledge_base/daily/.gitkeep` | - | ナレッジベース文書 |
| `knowledge_base/monthly/.gitkeep` | - | ナレッジベース文書 |
| `logs/.gitkeep` | - | ファイル |
| `scripts/install_task_scheduler.bat` | 581 B | ファイル |
| `scripts/run_daily.bat` | 207 B | ファイル |
| `src/writer/templates/email_template.html` | 5.4 KB | ファイル |

---

_自動生成: 2026-05-02 | 管理者: 男座員也（Kazuya Oza）_
