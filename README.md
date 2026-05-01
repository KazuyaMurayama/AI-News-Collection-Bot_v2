# AI News Collection Bot v2 — AIニュース自動収集・配信ボット（改良版）

> AI関連の最新ニュース・論文・ブログ記事を自動収集し、要約・タグ付けして配信するボットシステムのv2です。

## 📋 概要

AI関連の最新ニュース・論文・ブログ記事を自動収集し、要約・タグ付けして配信するボットシステムのv2です。v1を大幅改良し、精度・速度・カバレッジを向上させました。

## ✨ 主な機能

- AI/MLニュースの多ソース自動収集
- Claude APIによる日本語要約自動生成
- 重要度スコアリング・フィルタリング
- Slack / メール自動配信
- 収集ログ・重複排除機能

## 🛠️ 技術スタック

| カテゴリ | 技術・ライブラリ |
|----------|----------------|
| 言語 | Python 3.10+ |
| AI要約 | Claude API |
| スケジューリング | cron / schedule |
| データ管理 | SQLite / CSV |
| 通知 | Slack API / SMTP |

## 🚀 セットアップ

### 前提条件

- Python 3.9 以上
- APIキー（Claude / OpenAI 等）を `.env` ファイルに設定

### インストール

```bash
git clone https://github.com/KazuyaMurayama/AI-News-Collection-Bot_v2.git
cd AI-News-Collection-Bot_v2
pip install -r requirements.txt
```

### 環境設定

```bash
cp .env.example .env
# .env ファイルに必要なAPIキーを設定
```

## 💻 使い方

```bash
python bot.py
```

## 👨‍💻 開発者情報

**男座員也（Kazuya Oza / おざ かずや）**

| | |
|---|---|
| GitHub | [@KazuyaMurayama](https://github.com/KazuyaMurayama) |
| 専門領域 | データサイエンス・生成AIコンサルタント |
| 主要スキル | Python, LightGBM, LangChain, RAG, Streamlit, React, TypeScript |
| 事業 | AIコンサルティング（月単価目標300万円）/ SaaS開発 / 定量投資 |

## 📄 ライセンス

© 2025 男座員也（Kazuya Oza）. All rights reserved.

---

> このリポジトリは **男座員也（Kazuya Oza）** が開発・管理しています。
> 命名・ドキュメント等での表記は必ず **男座員也** または **Kazuya Oza** を使用してください。
