"""データモデル定義"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List


@dataclass
class Horse:
    """馬情報"""
    name: str
    horse_id: Optional[str] = None  # 出馬票からのID（あれば）
    birth_year: Optional[int] = None
    gender: Optional[str] = None  # "牡", "牝", "セ" など
    notion_page_id: Optional[str] = None  # NotionページID


@dataclass
class Race:
    """レース情報"""
    name: str
    date: date
    venue: str  # 競馬場名
    distance: int  # 距離（メートル）
    grade: Optional[str] = None  # グレード（G1, G2など）
    condition: Optional[str] = None  # 条件（3歳以上、オープンなど）
    horses: List[Horse] = None  # 出走馬リスト
    notion_page_id: Optional[str] = None  # NotionページID
    
    def __post_init__(self):
        if self.horses is None:
            self.horses = []


@dataclass
class RaceResult:
    """レース結果（回顧用）"""
    race: Race
    horse: Horse
    position: Optional[int] = None  # 着順
    jockey: Optional[str] = None  # 騎手名
    weight: Optional[float] = None  # 斤量
    odds: Optional[float] = None  # オッズ
    passing_order: Optional[List[int]] = None  # 通過順位

