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
            week_start: 対象週の開始日（ログ出力用、スクレイピングには影響なし）
        """
        print(f"回顧モード: アクティブな全てのレースを処理します (週基準: {week_start})")
        
        # 全レース情報を取得
        try:
            races = self.scraper.get_active_races(mode='retrospective')
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
                
                # レース結果情報を作成
                # 文字列から数値への変換を試みる
                pos = None
                try:
                    pos_str = horse.position
                    if pos_str and pos_str.isdigit():
                        pos = int(pos_str)
                except:
                    pass
                
                wgt = None
                try:
                    wgt_str = horse.weight
                    if wgt_str:
                        wgt = float(wgt_str)
                except:
                    pass

                race_result = RaceResult(
                    race=race,
                    horse=horse,
                    position=pos,
                    jockey=horse.jockey,
                    weight=wgt,
                    passing_order=horse.passing_order,
                    last_3f=horse.last_3f,
                    finish_time=horse.finish_time,
                    horse_weight=horse.horse_weight,
                    waku=horse.waku,
                    horse_number=horse.horse_number
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

