"""回顧モードの実装"""

from datetime import date, timedelta
from typing import List

from src.models import Race, Horse, RaceResult
from src.notion_client import NotionClient
from src.scraper import Scraper


class RetrospectiveUseCase:
    """回顧モードのユースケース"""
    
    def __init__(self, notion_client: NotionClient, scraper: Scraper):
        """
        初期化
        
        Args:
            notion_client: Notion APIクライアント
            scraper: スクレイパー
        """
        self.notion_client = notion_client
        self.scraper = scraper
    
    def execute(self, week_start: date) -> None:
        """
        回顧処理を実行
        
        Args:
            week_start: 対象週の開始日
        """
        print(f"回顧モード: {week_start} から1週間のレースを処理します")
        
        # その週の全レース情報を取得
        try:
            races = self.scraper.get_races_for_week(week_start)
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
            for horse in race.horses:
                print(f"  馬: {horse.name}")
                
                # 馬ページを検索または作成
                horse_page_id = self.notion_client.find_or_create_horse_page(horse.name)
                if not horse_page_id:
                    print(f"    エラー: 馬ページの作成に失敗しました")
                    continue
                
                horse.notion_page_id = horse_page_id
                
                # レース結果情報を作成（実際のデータはスクレイパーから取得する想定）
                race_result = RaceResult(
                    race=race,
                    horse=horse,
                    # 実際の実装では、スクレイパーから結果情報を取得
                    # position=...,
                    # jockey=...,
                    # weight=...,
                    # odds=...,
                )
                
                # 馬ページに出走履歴を追加
                success = self.notion_client.add_race_history_to_horse_page(
                    horse_page_id, race_result
                )
                
                if success:
                    print(f"    出走履歴を追加しました")
                else:
                    print(f"    エラー: 出走履歴の追加に失敗しました")
        
        print(f"\n処理完了: {len(races)}件のレースを処理しました")

