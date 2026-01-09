"""予想モードの実装"""

from datetime import date
from typing import List

from src.models import Race, Horse
from src.notion_client import NotionClient
from src.scraper import Scraper


class PredictionUseCase:
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
            race_date: 対象日（ログ出力用、スクレイピングには影響なし）
        """
        print(f"予想モード: アクティブな出馬票を処理します (基準日: {race_date})")
        
        # 全出馬票を取得
        try:
            races = self.scraper.get_active_races(mode='prediction', target_date=race_date)
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
            
            # 1. 各出走馬について馬ページを先に検索（メンション作成のため）
            print(f"  出走馬数: {len(race.horses)}頭")
            for horse in race.horses:
                horse_page_id = self.notion_client.find_horse_page(horse.name)
                horse.notion_page_id = horse_page_id
            
            # 2. レースページを作成（ここで出走馬リストも冒頭に追加される）
            race_page_id = self.notion_client.find_or_create_race_page(race)
            if not race_page_id:
                print(f"  エラー: レースページの作成に失敗しました")
                continue
            
            race.notion_page_id = race_page_id
            print(f"  レースページを処理しました")
        
        print(f"\n処理完了: {len(races)}件のレースを処理しました")
