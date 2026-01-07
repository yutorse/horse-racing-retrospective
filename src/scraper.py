"""出馬票・レース情報取得モジュール"""

from typing import List
from datetime import date

from src.models import Race, Horse


class Scraper:
    """出馬票・レース情報スクレイパー"""
    
    def __init__(self):
        """スクレイパーを初期化"""
        pass
    
    def get_races_for_week(self, week_start: date) -> List[Race]:
        """
        指定週の全レース情報を取得（回顧用）
        
        Args:
            week_start: 週の開始日
            
        Returns:
            レース情報のリスト
        """
        # TODO: 実装予定
        # JRA公式サイトまたはAPIからレース情報を取得
        raise NotImplementedError("get_races_for_weekは未実装です")
    
    def get_race_entries(self, race_date: date) -> List[Race]:
        """
        指定日の出馬票を取得（予想用）
        
        Args:
            race_date: レース開催日
            
        Returns:
            レース情報のリスト（出走馬情報含む）
        """
        # TODO: 実装予定
        # 出馬票からレース情報と出走馬情報を取得
        raise NotImplementedError("get_race_entriesは未実装です")

