"""Notion API操作モジュール"""

from typing import Optional, List, Dict, Any
from datetime import date
from notion_client import Client
from notion_client.api_endpoints import Endpoint
import requests

from src.config import Config
from src.models import Race, Horse, RaceResult


class NotionClient:
    """Notion APIクライアント"""
    
    def __init__(self):
        """Notionクライアントを初期化"""
        Config.validate()
        self.client = Client(auth=Config.NOTION_API_KEY)
        self.horse_db_id = Config.NOTION_HORSE_DB_ID
        self.race_db_id = Config.NOTION_RACE_DB_ID
    
    def find_horse_page(self, horse_name: str) -> Optional[str]:
        """
        馬名で馬ページを検索
        
        Args:
            horse_name: 馬名
            
        Returns:
            ページID（見つからない場合はNone）
        """
        try:
            # Notion APIの正しい使い方: POST /v1/databases/{database_id}/query
            # notion-clientのdatabases.query()が使えないため、直接HTTPリクエストを送信
            url = f"https://api.notion.com/v1/databases/{self.horse_db_id}/query"
            headers = {
                "Authorization": f"Bearer {Config.NOTION_API_KEY}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            payload = {
                "filter": {
                    "property": "馬名",  # プロパティ名は実際のNotion DBに合わせて調整
                    "title": {
                        "equals": horse_name
                    }
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                return data["results"][0]["id"]
            return None
        except Exception as e:
            print(f"馬ページ検索エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_horse_page(self, horse_name: str) -> Optional[str]:
        """
        馬ページを作成
        
        Args:
            horse_name: 馬名
            
        Returns:
            作成されたページID
        """
        try:
            response = self.client.pages.create(
                parent={"database_id": self.horse_db_id},
                properties={
                    "馬名": {
                        "title": [
                            {
                                "text": {
                                    "content": horse_name
                                }
                            }
                        ]
                    }
                }
            )
            return response["id"]
        except Exception as e:
            print(f"馬ページ作成エラー: {e}")
            return None
    
    def find_or_create_horse_page(self, horse_name: str) -> Optional[str]:
        """
        馬ページを検索、なければ作成
        
        Args:
            horse_name: 馬名
            
        Returns:
            ページID
        """
        page_id = self.find_horse_page(horse_name)
        if page_id:
            return page_id
        
        return self.create_horse_page(horse_name)
    
    def find_race_page(self, race_name: str, race_date: date) -> Optional[str]:
        """
        レース名と日付でレースページを検索
        
        Args:
            race_name: レース名
            race_date: レース開催日
            
        Returns:
            ページID（見つからない場合はNone）
        """
        try:
            # Notion APIの正しい使い方: POST /v1/databases/{database_id}/query
            # notion-clientのdatabases.query()が使えないため、直接HTTPリクエストを送信
            url = f"https://api.notion.com/v1/databases/{self.race_db_id}/query"
            headers = {
                "Authorization": f"Bearer {Config.NOTION_API_KEY}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            payload = {
                "filter": {
                    "and": [
                        {
                            "property": "レース名",  # プロパティ名は実際のNotion DBに合わせて調整
                            "title": {
                                "equals": race_name
                            }
                        },
                        {
                            "property": "開催日",  # プロパティ名は実際のNotion DBに合わせて調整
                            "date": {
                                "equals": race_date.isoformat()
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                return data["results"][0]["id"]
            return None
        except Exception as e:
            print(f"レースページ検索エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_race_page(self, race: Race) -> Optional[str]:
        """
        レースページを作成
        
        Args:
            race: レース情報
            
        Returns:
            作成されたページID
        """
        try:
            # レース名のタイトルを作成
            title = f"{race.date.strftime('%Y-%m-%d')} {race.venue} {race.name}"
            
            properties: Dict[str, Any] = {
                "レース名": {  # プロパティ名は実際のNotion DBに合わせて調整
                    "title": [
                        {
                            "text": {
                                "content": race.name
                            }
                        }
                    ]
                },
                "開催日": {  # プロパティ名は実際のNotion DBに合わせて調整
                    "date": {
                        "start": race.date.isoformat()
                    }
                },
                "競馬場": {  # プロパティ名は実際のNotion DBに合わせて調整
                    # multi_selectが期待されている場合はmulti_selectを使用
                    "multi_select": [
                        {
                            "name": race.venue
                        }
                    ]
                },
                "距離": {  # プロパティ名は実際のNotion DBに合わせて調整
                    # multi_selectが期待されている場合はmulti_selectを使用
                    "multi_select": [
                        {
                            "name": str(race.distance)
                        }
                    ]
                }
            }
            
            # グレードがある場合は追加
            if race.grade:
                properties["グレード"] = {  # プロパティ名は実際のNotion DBに合わせて調整
                    # multi_selectが期待されている場合はmulti_selectを使用
                    "multi_select": [
                        {
                            "name": race.grade
                        }
                    ]
                }
            
            # 条件がある場合は追加
            if race.condition:
                properties["条件"] = {  # プロパティ名は実際のNotion DBに合わせて調整
                    # multi_selectが期待されている場合はmulti_selectを使用
                    "multi_select": [
                        {
                            "name": race.condition
                        }
                    ]
                }
            
            response = self.client.pages.create(
                parent={"database_id": self.race_db_id},
                properties=properties
            )
            
            page_id = response["id"]
            
            # 初期コンテンツを追加
            self._add_race_initial_blocks(page_id, race)
            
            return page_id
        except Exception as e:
            print(f"レースページ作成エラー: {e}")
            return None
    
    def find_or_create_race_page(self, race: Race) -> Optional[str]:
        """
        レースページを検索、なければ作成
        
        Args:
            race: レース情報
            
        Returns:
            ページID
        """
        page_id = self.find_race_page(race.name, race.date)
        if page_id:
            return page_id
        
        return self.create_race_page(race)
    
    def add_horse_link_to_race_page(self, race_page_id: str, horse_page_id: str, horse_name: str) -> bool:
        """
        レースページに出走馬のリンクを追加
        
        Args:
            race_page_id: レースページID
            horse_page_id: 馬ページID
            horse_name: 馬名（表示用）
            
        Returns:
            成功したかどうか
        """
        try:
            # 出走馬セクションにリンクを追加
            block = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "mention",
                            "mention": {
                                "page": {
                                    "id": horse_page_id
                                }
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f" - {horse_name}"
                            }
                        }
                    ]
                }
            }
            
            self.client.blocks.children.append(
                block_id=race_page_id,
                children=[block]
            )
            return True
        except Exception as e:
            print(f"出走馬リンク追加エラー: {e}")
            return False
    
    def add_race_history_to_horse_page(self, horse_page_id: str, race_result: RaceResult) -> bool:
        """
        馬ページに出走履歴を追加
        
        Args:
            horse_page_id: 馬ページID
            race_result: レース結果情報
            
        Returns:
            成功したかどうか
        """
        try:
            race = race_result.race
            horse = race_result.horse
            
            # レース情報のブロックを作成
            race_info = f"{race.date.strftime('%Y-%m-%d')} {race.venue} {race.name}"
            if race_result.position:
                race_info += f" ({race_result.position}着)"
            
            blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": race_info
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "mention",
                                "mention": {
                                    "page": {
                                        "id": race.notion_page_id
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
            
            # レース結果の詳細情報を追加
            details = []
            if race_result.jockey:
                details.append(f"騎手: {race_result.jockey}")
            if race_result.weight:
                details.append(f"斤量: {race_result.weight}kg")
            if race_result.odds:
                details.append(f"オッズ: {race_result.odds}")
            
            if details:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": " | ".join(details)
                                }
                            }
                        ]
                    }
                })
            
            # 回顧メモ用のテンプレートを追加
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "展開・ポジション"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": []
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "上がり・脚質"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": []
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "総評"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": []
                    }
                }
            ])
            
            self.client.blocks.children.append(
                block_id=horse_page_id,
                children=blocks
            )
            return True
        except Exception as e:
            print(f"出走履歴追加エラー: {e}")
            return False
    
    def _add_race_initial_blocks(self, race_page_id: str, race: Race) -> None:
        """
        レースページに初期ブロックを追加
        
        Args:
            race_page_id: レースページID
            race: レース情報
        """
        try:
            blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "出走馬"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "出走馬のメモへのリンク:"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "予想のポイント"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": []
                    }
                }
            ]
            
            self.client.blocks.children.append(
                block_id=race_page_id,
                children=blocks
            )
        except Exception as e:
            print(f"初期ブロック追加エラー: {e}")

