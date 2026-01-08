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
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "メモ"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [],
                            "language": "plain text"
                        }
                    }
                ]
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
    
    def find_race_page(self, race_name: str, race_date: date, venue: str, race_number: Optional[int]) -> Optional[str]:
        """
        レース名、日付、競馬場、レース番号でレースページを検索
        
        Args:
            race_name: レース名
            race_date: レース開催日
            venue: 競馬場
            race_number: レース番号
            
        Returns:
            ページID（見つからない場合はNone）
        """
        try:
            url = f"https://api.notion.com/v1/databases/{self.race_db_id}/query"
            headers = {
                "Authorization": f"Bearer {Config.NOTION_API_KEY}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            and_filter = [
                {
                    "property": "開催日",
                    "date": {
                        "equals": race_date.isoformat()
                    }
                },
                {
                    "property": "競馬場",
                    "multi_select": {
                        "contains": venue
                    }
                }
            ]
            
            if race_number:
                and_filter.append({
                    "property": "R",
                    "number": {
                        "equals": race_number
                    }
                })
            
            # デバッグログを追加
            # print(f"  Notion検索フィルター: {and_filter}")

            payload = {
                "filter": {
                    "and": and_filter
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"  Notion APIエラー ({response.status_code}): {response.text}")
                # 失敗した場合はレース名のみで再試行（フォールバック）
                if race_number:
                    print("  Rでの検索に失敗しました。レース名のみで再試行します。")
                    return self.find_race_page(race_name, race_date, venue, None)
                return None

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
                properties["条件"] = {
                    "multi_select": [
                        {
                            "name": race.condition
                        }
                    ]
                }
            
            # レース番号がある場合は追加
            if race.race_number:
                properties["R"] = {
                    "number": race.race_number
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
        page_id = self.find_race_page(race.name, race.date, race.venue, race.race_number)
        if page_id:
            # レース名が「詳細不明」の場合は更新を試みる
            if race.name and race.name != "レース詳細不明":
                try:
                    self.client.pages.update(
                        page_id=page_id,
                        properties={
                            "レース名": {
                                "title": [{"text": {"content": race.name}}]
                            }
                        }
                    )
                except Exception:
                    pass
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
    
    def add_horses_to_race_page(self, race_page_id: str, horses: List[Horse]) -> bool:
        """
        レースページに出走馬の一覧を追加
        
        Args:
            race_page_id: レースページID
            horses: 馬情報のリスト
            
        Returns:
            成功したかどうか
        """
        try:
            children = []
            for horse in horses:
                rich_text = []
                # 1. 馬名部分 (メンションまたはテキスト)
                if horse.notion_page_id:
                    rich_text.append({
                        "type": "mention",
                        "mention": {
                            "page": {
                                "id": horse.notion_page_id
                            }
                        }
                    })
                else:
                    rich_text.append({
                        "type": "text",
                        "text": {
                            "content": horse.name
                        }
                    })
                
                # 2. 追加情報 (性齢 騎手 斤量)
                # 性齢は "牝3", 斤量は "54.0" 等
                details = f" {horse.gender or ''}{horse.age or ''} {horse.jockey or '不明'} {horse.weight or ''}"
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": details
                    }
                })
                
                # 箇条書きではなくパラグラフ（1頭1行）
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text
                    }
                })

            if children:
                self.client.blocks.children.append(
                    block_id=race_page_id,
                    children=children
                )
            return True
        except Exception as e:
            print(f"出走馬リスト追加エラー: {e}")
            return False

    def _ensure_past_races_section(self, page_id: str) -> None:
        """
        馬ページ内に「過去レース」セクション（見出し2）があることを確認し、なければ作成する
        """
        try:
            blocks = self.client.blocks.children.list(block_id=page_id)
            for block in blocks.get("results", []):
                if block["type"] == "heading_2":
                    text = "".join([t["plain_text"] for t in block["heading_2"]["rich_text"]])
                    if "過去レース" in text:
                        return
            
            # 見つからない場合はページ末尾に作成
            self.client.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "過去レース"}}]
                        }
                    }
                ]
            )
        except Exception as e:
            print(f"過去レースセクション確認エラー: {e}")

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
            
            # 過去レース見出しがあることを確認
            self._ensure_past_races_section(horse_page_id)
            
            # レースページのIDがない場合は検索
            if not race.notion_page_id:
                race.notion_page_id = self.find_race_page(race.name, race.date, race.venue, race.race_number)

            # レース情報のタイトル (H3)
            # レース番号（R）があれば含める
            r_str = f"{race.race_number}R " if race.race_number else ""
            race_info = f"{race.date.strftime('%Y-%m-%d')} {race.venue} {r_str}{race.name}"
            race_info = race_info.replace("JRA", "").strip()
            if race_result.position:
                race_info += f" ({race_result.position}着)"
            
            # レース詳細情報
            # 行1: タイム、上がり、馬体重
            line1 = f"タイム: {race_result.finish_time if race_result.finish_time else '取得失敗'} | 上がり: {race_result.last_3f if race_result.last_3f else '取得失敗'} | 馬体重: {race_result.horse_weight if race_result.horse_weight else '取得失敗'}"
            # 行2: 競馬場、コース、距離、馬場状況
            # track_typeに詳細（ダート・右等）が入っている前提
            track_info = f"{race.distance}m ({race.track_type if race.track_type else '芝'})"
            line2 = f"競馬場: {race.venue} | {track_info} | 馬場: {race.track_condition if race.track_condition else '良'}"
            # 行3: 騎手、斤量
            line3 = f"騎手: {race_result.jockey} | 斤量: {race_result.weight}kg"

            # ラップタイム整形
            lap_text = "取得失敗"
            if race.lap_time:
                try:
                    laps = [l.strip() for l in race.lap_time.split('-') if l.strip()]
                    formatted_laps = "-".join(laps)
                    lap_floats = []
                    for l in laps:
                        try:
                            lap_floats.append(float(l))
                        except:
                            continue
                    if lap_floats:
                        first_3 = sum(lap_floats[:3])
                        last_3 = sum(lap_floats[-3:])
                        lap_text = f"{formatted_laps} ({first_3:.1f}-{last_3:.1f})"
                    else:
                        lap_text = formatted_laps
                except Exception as e:
                    print(f"ラップタイム整形エラー: {e}")
                    lap_text = race.lap_time

            # ポジション整形
            pos_text = "取得失敗"
            if race_result.passing_order:
                raw_pos = race_result.passing_order.strip()
                if '-' in raw_pos:
                    pos_text = raw_pos
                elif ' ' in raw_pos:
                    pos_text = "-".join(raw_pos.split())
                else:
                    pos_text = raw_pos

            # 行3: 騎手、斤量
            line3 = f"騎手: {race_result.jockey} | 斤量: {race_result.weight}kg"
            # 行4: ラップ、上がり、ポジション
            line4 = f"ラップ: {lap_text} | 上がり: {race_result.last_3f if race_result.last_3f else '取得失敗'} | ポジション: {pos_text}"

            # 追加するブロックのリスト
            blocks = [
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": race_info}}]
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
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line1}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line2}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line3}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line4}}]
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
                                    "content": "レースメモ"
                                },
                                "annotations": {"bold": True}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [],
                        "language": "plain text"
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                }
            ]

            # ページ末尾に追記
            self.client.blocks.children.append(
                block_id=horse_page_id,
                children=blocks
            )
            return True
        except Exception as e:
            print(f"出走履歴追加エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_race_initial_blocks(self, race_page_id: str, race: Race) -> None:
        """
        レースページに初期ブロックを追加 (出走馬リストを表形式で冒頭に配置)
        
        Args:
            race_page_id: レースページID
            race: レース情報
        """
        try:
            # テーブルの行を作成
            table_rows = []
            
            # ヘッダー行 (6列)
            header_row = {
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"type": "text", "text": {"content": "印"}}],
                        [{"type": "text", "text": {"content": "馬名"}}],
                        [{"type": "text", "text": {"content": "性齢"}}],
                        [{"type": "text", "text": {"content": "騎手"}}],
                        [{"type": "text", "text": {"content": "斤量"}}],
                        [{"type": "text", "text": {"content": "メモ"}}]
                    ]
                }
            }
            table_rows.append(header_row)
            
            # 各馬の行
            for horse in race.horses:
                # 馬名セル (メンションまたはテキスト)
                name_cell = []
                if horse.notion_page_id:
                    name_cell.append({
                        "type": "mention",
                        "mention": {"page": {"id": horse.notion_page_id}}
                    })
                else:
                    name_cell.append({
                        "type": "text",
                        "text": {"content": horse.name}
                    })
                
                row = {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": [
                            [], # 印 (空)
                            name_cell,
                            [{"type": "text", "text": {"content": f"{horse.gender or ''}{horse.age or ''}"}}],
                            [{"type": "text", "text": {"content": horse.jockey or ''}}],
                            [{"type": "text", "text": {"content": horse.weight or ''}}],
                            []  # メモ (空)
                        ]
                    }
                }
                table_rows.append(row)

            blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "出走馬"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": 6,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": table_rows
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "予想"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": []}
                }
            ]
            
            self.client.blocks.children.append(
                block_id=race_page_id,
                children=blocks
            )
        except Exception as e:
            print(f"初期ブロック追加エラー: {e}")
            import traceback
            traceback.print_exc()
