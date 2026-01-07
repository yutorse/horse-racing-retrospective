# 競馬レース回顧メモ自動化ツール

競馬のレースを回顧したメモを Notion に残すための自動化ツールです。

## 機能

### 1. 回顧時（Retrospective）

その週にあった全レースの情報を取得し、出走していた馬に対してメモを作成します。
すでにメモが存在している馬については、そのメモに加筆する形になります。

### 2. 予想時（Forecast）

出馬票が確定したら、その週のレース 1 つにつき、1 つのメモを作成します。
各メモにはそのレースに出る出走馬の馬メモを全て貼るようにします。

## セットアップ

### 1. 必要なツール

- [mise](https://mise.jdx.dev/) - バージョン管理ツール
- [uv](https://github.com/astral-sh/uv) - Python パッケージマネージャー（mise で自動インストール）

### 2. プロジェクトのセットアップ

```bash
# miseでPython環境とuvをセットアップ
mise install

# 仮想環境を作成し、依存パッケージをインストール
mise run setup
```

### 3. Notion API の設定

1. [Notion Integrations](https://www.notion.so/my-integrations) でインテグレーションを作成
2. インテグレーショントークンを取得
3. Notion で以下のデータベースを作成：
   - **馬データベース**: 馬メモ用
   - **レースデータベース**: レースメモ用
4. 各データベースにインテグレーションのアクセス権限を付与（データベースページの右上「...」→「接続」→ インテグレーションを選択）
5. 各データベースの ID を取得

### 4. 環境変数の設定

`mise.toml`に環境変数を設定します：

```toml
[env]
NOTION_API_KEY = "your_notion_api_key"
NOTION_HORSE_DB_ID = "your_horse_db_id"
NOTION_RACE_DB_ID = "your_race_db_id"
```

## 使用方法

### 回顧モード

```bash
# 指定週のレースを回顧
mise run retrospective 2025-01-13
```

### 予想モード

```bash
# 指定日の出馬票からレースメモを作成
mise run forecast 2025-01-17
```

### その他の実行方法

```bash
# 直接uv runで実行する場合
mise run uv run src/main.py --mode retrospective --week 2025-01-13
mise run uv run src/main.py --mode forecast --date 2025-01-17
```

## プロジェクト構造

```
horse-racing-retrospective/
├── src/
│   ├── __init__.py
│   ├── config.py          # 設定管理
│   ├── models.py           # データモデル
│   ├── notion_client.py    # Notion API操作
│   ├── scraper.py          # 出馬票取得
│   └── main.py             # メインエントリーポイント
├── scripts/                # 実行スクリプト（今後追加）
├── mise.toml               # mise設定
├── requirements.txt        # Python依存関係
└── README.md
```

## 開発状況

- [x] プロジェクト基本構造
- [x] mise 設定と環境変数管理
- [ ] Notion API 操作（馬ページ作成・検索）
- [ ] 出馬票取得機能
- [ ] 回顧モード実装
- [ ] 予想モード実装

## ライセンス

MIT
