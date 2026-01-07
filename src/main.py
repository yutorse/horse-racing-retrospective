"""メインエントリーポイント"""

import argparse
from datetime import date, timedelta
from typing import Optional

from src.config import Config
from src.notion_client import NotionClient
from src.scraper import Scraper
from src.usecases.retrospective import RetrospectiveUseCase
from src.usecases.forecast import ForecastUseCase


def parse_date(date_str: str) -> date:
    """
    日付文字列をパース
    
    Args:
        date_str: YYYY-MM-DD形式の日付文字列
        
    Returns:
        dateオブジェクト
    """
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"無効な日付形式です: {date_str} (YYYY-MM-DD形式で指定してください)")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="競馬レース回顧メモ自動化ツール")
    parser.add_argument(
        "--mode",
        choices=["retrospective", "forecast"],
        required=True,
        help="実行モード: retrospective（回顧）またはforecast（予想）"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="対象日（YYYY-MM-DD形式）。forecastモードで使用"
    )
    parser.add_argument(
        "--week",
        type=str,
        help="対象週の開始日（YYYY-MM-DD形式）。retrospectiveモードで使用"
    )
    
    args = parser.parse_args()
    
    # 設定検証
    try:
        Config.validate()
    except ValueError as e:
        print(f"エラー: {e}")
        return 1
    
    # クライアントとスクレイパーを初期化
    notion_client = NotionClient()
    scraper = Scraper()
    
    # モード別処理
    try:
        if args.mode == "retrospective":
            if not args.week:
                print("エラー: retrospectiveモードでは--weekオプションが必要です")
                return 1
            
            week_start = parse_date(args.week)
            usecase = RetrospectiveUseCase(notion_client, scraper)
            usecase.execute(week_start)
            
        elif args.mode == "forecast":
            if not args.date:
                print("エラー: forecastモードでは--dateオプションが必要です")
                return 1
            
            race_date = parse_date(args.date)
            usecase = ForecastUseCase(notion_client, scraper)
            usecase.execute(race_date)
    
    except ValueError as e:
        print(f"エラー: {e}")
        return 1
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

