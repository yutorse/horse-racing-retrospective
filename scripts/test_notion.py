"""Notion API動作確認スクリプト"""

import sys
import os
from datetime import date
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.notion_client import NotionClient
from src.models import Race, Horse


def test_config():
    """設定の確認"""
    print("=== 設定確認 ===")
    try:
        Config.validate()
        print("✓ 環境変数が正しく設定されています")
        print(f"  NOTION_HORSE_DB_ID: {Config.NOTION_HORSE_DB_ID[:8]}...")
        print(f"  NOTION_RACE_DB_ID: {Config.NOTION_RACE_DB_ID[:8]}...")
        return True
    except ValueError as e:
        print(f"✗ エラー: {e}")
        return False


def test_notion_connection():
    """Notion API接続確認"""
    print("\n=== Notion API接続確認 ===")
    try:
        client = NotionClient()
        print("✓ NotionClientの初期化に成功しました")
        return client
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_horse_page_operations(client: NotionClient):
    """馬ページ操作のテスト"""
    print("\n=== 馬ページ操作テスト ===")
    
    test_horse_name = "テスト馬"
    
    # 1. 馬ページの検索（存在しない場合）
    print(f"\n1. 馬ページの検索: {test_horse_name}")
    page_id = client.find_horse_page(test_horse_name)
    if page_id:
        print(f"  ✓ 既存のページが見つかりました: {page_id}")
    else:
        print(f"  ✓ ページが見つかりませんでした（新規作成が必要）")
    
    # 2. 馬ページの作成
    print(f"\n2. 馬ページの作成: {test_horse_name}")
    page_id = client.create_horse_page(test_horse_name)
    if page_id:
        print(f"  ✓ ページを作成しました: {page_id}")
        print(f"  URL: https://www.notion.so/{page_id.replace('-', '')}")
    else:
        print(f"  ✗ ページの作成に失敗しました")
        return False
    
    # 3. 再度検索（今度は見つかるはず）
    print(f"\n3. 作成したページの検索: {test_horse_name}")
    found_id = client.find_horse_page(test_horse_name)
    if found_id == page_id:
        print(f"  ✓ 作成したページが見つかりました")
    else:
        print(f"  ⚠ ページIDが一致しません（期待: {page_id}, 実際: {found_id}）")
    
    # 4. find_or_create_horse_pageのテスト
    print(f"\n4. find_or_create_horse_pageのテスト")
    existing_id = client.find_or_create_horse_page(test_horse_name)
    if existing_id == page_id:
        print(f"  ✓ 既存のページを正しく取得しました")
    else:
        print(f"  ⚠ 予期しない動作（期待: {page_id}, 実際: {existing_id}）")
    
    return True


def test_race_page_operations(client: NotionClient):
    """レースページ操作のテスト"""
    print("\n=== レースページ操作テスト ===")
    
    # テスト用のレースデータを作成
    test_race = Race(
        name="テストレース",
        date=date.today(),
        venue="東京",
        distance=1600,
        grade="G1",
        condition="3歳以上"
    )
    
    # 1. レースページの検索（存在しない場合）
    print(f"\n1. レースページの検索: {test_race.name}")
    page_id = client.find_race_page(test_race.name, test_race.date)
    if page_id:
        print(f"  ✓ 既存のページが見つかりました: {page_id}")
    else:
        print(f"  ✓ ページが見つかりませんでした（新規作成が必要）")
    
    # 2. レースページの作成
    print(f"\n2. レースページの作成: {test_race.name}")
    page_id = client.create_race_page(test_race)
    if page_id:
        print(f"  ✓ ページを作成しました: {page_id}")
        print(f"  URL: https://www.notion.so/{page_id.replace('-', '')}")
        test_race.notion_page_id = page_id
    else:
        print(f"  ✗ ページの作成に失敗しました")
        return False
    
    # 3. 再度検索（今度は見つかるはず）
    print(f"\n3. 作成したページの検索: {test_race.name}")
    found_id = client.find_race_page(test_race.name, test_race.date)
    if found_id == page_id:
        print(f"  ✓ 作成したページが見つかりました")
    else:
        print(f"  ⚠ ページIDが一致しません（期待: {page_id}, 実際: {found_id}）")
    
    return test_race


def test_link_operations(client: NotionClient, race: Race):
    """リンク操作のテスト"""
    print("\n=== リンク操作テスト ===")
    
    # テスト用の馬データを作成
    test_horse = Horse(name="テスト出走馬")
    horse_page_id = client.find_or_create_horse_page(test_horse.name)
    
    if not horse_page_id:
        print("✗ 馬ページの作成に失敗しました")
        return False
    
    print(f"✓ テスト用馬ページ: {horse_page_id}")
    
    # レースページに出走馬リンクを追加
    print(f"\n1. レースページに出走馬リンクを追加")
    success = client.add_horse_link_to_race_page(
        race.notion_page_id, horse_page_id, test_horse.name
    )
    
    if success:
        print(f"  ✓ リンクを追加しました")
        print(f"  レースページを確認してください: https://www.notion.so/{race.notion_page_id.replace('-', '')}")
    else:
        print(f"  ✗ リンクの追加に失敗しました")
        return False
    
    return True


def main():
    """メイン処理"""
    print("Notion API動作確認を開始します\n")
    
    # 1. 設定確認
    if not test_config():
        return 1
    
    # 2. Notion接続確認
    client = test_notion_connection()
    if not client:
        return 1
    
    # 3. 馬ページ操作テスト
    if not test_horse_page_operations(client):
        print("\n⚠ 馬ページ操作テストで問題が発生しました")
        return 1
    
    # 4. レースページ操作テスト
    race = test_race_page_operations(client)
    if not race:
        print("\n⚠ レースページ操作テストで問題が発生しました")
        return 1
    
    # 5. リンク操作テスト
    if not test_link_operations(client, race):
        print("\n⚠ リンク操作テストで問題が発生しました")
        return 1
    
    print("\n" + "="*50)
    print("✓ すべてのテストが完了しました！")
    print("="*50)
    print("\nNotionで以下のページを確認してください：")
    print(f"- 馬データベース: テスト馬")
    print(f"- レースデータベース: テストレース")
    
    return 0


if __name__ == "__main__":
    exit(main())

