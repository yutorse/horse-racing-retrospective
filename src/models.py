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
    age: Optional[str] = None  # "3", "4" など
    notion_page_id: Optional[str] = None  # NotionページID
    
    # レース結果データ (スクレイピング用一時保持)
    position: Optional[str] = None
    jockey: Optional[str] = None
    weight: Optional[str] = None
    odds: Optional[str] = None
    passing_order: Optional[str] = None
    last_3f: Optional[str] = None
    finish_time: Optional[str] = None
    horse_weight: Optional[str] = None
    waku: Optional[str] = None  # 枠番
    horse_number: Optional[str] = None  # 馬番


@dataclass
class Race:
    """レース情報"""
    name: str
    date: date
    venue: str  # 競馬場名
    distance: int  # 距離（メートル）
    grade: Optional[str] = None  # グレード（G1, G2など）
    condition: Optional[str] = None  # 条件（3歳以上、オープンなど）
    track_type: Optional[str] = None  # 芝/ダート/障害
    track_condition: Optional[str] = None  # 馬場状態 (良、重など)
    race_number: Optional[int] = None  # レース番号 (1-12)
    horses: List[Horse] = None  # 出走馬リスト
    lap_time: Optional[str] = None  # ラップタイム
    notion_page_id: Optional[str] = None  # NotionページID
    # 映像URL生成用の追加データ
    kaisai_number: Optional[str] = None  # 第N回のN
    kaisai_day: Optional[str] = None     # 第N日のN
    venue_id: Optional[str] = None       # 競馬場ID (1-a)
    
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
    passing_order: Optional[str] = None  # 通過順位
    last_3f: Optional[str] = None  # 上がり3F
    finish_time: Optional[str] = None  # タイム
    horse_weight: Optional[str] = None  # 馬体重
    waku: Optional[str] = None  # 枠番
    horse_number: Optional[str] = None  # 馬番

