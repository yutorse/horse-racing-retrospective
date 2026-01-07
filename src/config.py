"""設定管理モジュール"""

import os
from typing import Optional


class Config:
    """アプリケーション設定"""
    
    # Notion API設定
    NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
    NOTION_HORSE_DB_ID: str = os.getenv("NOTION_HORSE_DB_ID", "")
    NOTION_RACE_DB_ID: str = os.getenv("NOTION_RACE_DB_ID", "")
    
    @classmethod
    def validate(cls) -> None:
        """必須環境変数の検証"""
        missing = []
        
        if not cls.NOTION_API_KEY:
            missing.append("NOTION_API_KEY")
        if not cls.NOTION_HORSE_DB_ID:
            missing.append("NOTION_HORSE_DB_ID")
        if not cls.NOTION_RACE_DB_ID:
            missing.append("NOTION_RACE_DB_ID")
        
        if missing:
            raise ValueError(
                f"以下の環境変数が設定されていません: {', '.join(missing)}\n"
                f"mise.tomlで設定するか、mise setコマンドで設定してください。\n"
                f"例: mise set NOTION_API_KEY=your_api_key"
            )

