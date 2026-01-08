# 競馬レース回顧メモ自動化ツール

競馬のレースを回顧したメモを Notion に残すための自動化ツールです。

## 機能

### 1. 回顧時（Retrospective）

その週にあった全レースの情報を取得し、出走していた馬に対してメモを作成します。
すでにメモが存在している馬については、そのメモに加筆する形になります。

### 2. 予想時（Prediction）

出馬票からその週のレースごとにノートを作成します。
- **出走馬一覧の自動生成**: 表形式（馬名、性齢、騎手、斤量）で出走馬を一覧表示。
- **馬ページへの自動リンク**: すでにメモが存在する馬については、自動的に `@メンション` でリンクを貼ります。
- **精密なデータ抽出**: JRA サイトから馬名、性別、年齢、騎手、斤量を正確に取得します。

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

#### データベースのプロパティ設定

**馬データベース**に以下のプロパティが必要です：

- `名前` (Title) - 必須

**レースデータベース**に以下のプロパティが必要です：

- `レース名` (Title) - 必須
- `開催日` (Date) - 必須
- `競馬場` (Select) - 必須
- `R` (Number) - 必須
- `距離` (Number) - 必須
- `グレード` (Select) - オプション
- `条件` (Rich Text) - オプション

**注意**: プロパティ名は実際の Notion データベースのプロパティ名と一致させる必要があります。
プロパティ名が異なる場合は、`src/notion_client.py`の該当箇所を編集してください。

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
mise run retrospective
```

### 予想モード

```bash
# 指定日の出馬票からレースメモを作成
mise run prediction
```

### その他の実行方法

```bash
# 直接uv runで実行する場合
mise run uv run src/main.py --mode retrospective --week 2025-01-13
mise run uv run src/main.py --mode prediction --date 2025-01-17
```

### 動作確認

Notion API の接続と基本的な操作をテストするには：

```bash
mise run test-notion
```

このスクリプトは以下をテストします：

- 環境変数の設定確認
- Notion API 接続確認
- 馬ページの作成・検索
- レースページの作成・検索
- ページ間のリンク追加

テスト実行後、Notion で「テスト馬」と「テストレース」のページが作成されていることを確認してください。

## プロジェクト構造

```
horse-racing-retrospective/
├── src/
│   ├── __init__.py
│   ├── config.py              # 設定管理
│   ├── models.py              # データモデル
│   ├── notion_client.py       # Notion API操作
│   ├── scraper.py             # 出馬票取得
│   ├── main.py                # メインエントリーポイント
│   └── usecases/              # ユースケース
│       ├── __init__.py
│       ├── retrospective.py  # 回顧モード
│       └── prediction.py        # 予想モード
├── scripts/                   # 実行スクリプト（今後追加）
├── mise.toml                  # mise設定
├── requirements.txt           # Python依存関係
└── README.md
```

## 開発状況

- [x] プロジェクト基本構造
- [x] mise 設定と環境変数管理
- [x] Notion API 操作（馬ページ作成・検索）
- [x] Notion API 操作（レースページ作成・検索）
- [x] ページブロック追加機能（テーブル・メンション対応）
- [x] 回顧モード実装
- [x] 予想モード実装
- [x] JRA スクレイパー実装（精密抽出対応）
- [x] レース特定ロジック（日付・競馬場・レース番号による重複回避）

## ライセンス

MIT
