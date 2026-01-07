"""予想モードの実装"""

from datetime import date
from typing import List

from src.models import Race, Horse
from src.notion_client import NotionClient
from src.scraper import Scraper


class ForecastUseCase:
    """予想モードのユースケース"""
    
    def __init__(self, notion_client: NotionClient, scraper: Scraper):
        """
        初期化
        
        Args:
            notion_client: Notion APIクライアント
            scraper: スクレイパー
        """
        self.notion_client = notion_client
        self.scraper = scraper
    
    def execute(self, race_date: date) -> None:
        """
        予想処理を実行
        
        Args:
            race_date: 対象日
        """
        print(f"予想モード: {race_date} の出馬票を処理します")
        
        # 指定日の出馬票を取得
        try:
            races = self.scraper.get_race_entries(race_date)
        except NotImplementedError:
            print("エラー: 出馬票取得機能が未実装です")
            return
        
        if not races:
            print("該当するレースが見つかりませんでした")
            return
        
        print(f"{len(races)}件のレースが見つかりました")
        
        # 各レースについて処理
        for race in races:
            print(f"\n処理中: {race.date} {race.venue} {race.name}")
            
            # レースページを作成（既に存在する場合は取得）
            race_page_id = self.notion_client.find_or_create_race_page(race)
            if not race_page_id:
                print(f"  エラー: レースページの作成に失敗しました")
                continue
            
            race.notion_page_id = race_page_id
            
            # 各出走馬について処理
            print(f"  出走馬数: {len(race.horses)}頭")
            
            for horse in race.horses:
                print(f"    馬: {horse.name}")
                
                # 馬ページを検索または作成
                horse_page_id = self.notion_client.find_or_create_horse_page(horse.name)
                if not horse_page_id:
                    print(f"      エラー: 馬ページの作成に失敗しました")
                    continue
                
                horse.notion_page_id = horse_page_id
                
                # レースページに出走馬のリンクを追加
                success = self.notion_client.add_horse_link_to_race_page(
                    race_page_id, horse_page_id, horse.name
                )
                
                if success:
                    print(f"      リンクを追加しました")
                else:
                    print(f"      エラー: リンクの追加に失敗しました")
        
        print(f"\n処理完了: {len(races)}件のレースを処理しました")

