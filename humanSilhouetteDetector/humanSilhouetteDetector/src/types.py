"""レイヤ間で受け渡すデータ構造.

詳細設計書「1. データ構造定義」に対応します。
認識層の出力（RecognitionResult）は素の numpy 配列のみを保持し、
MediaPipe 固有の型に依存しません。これにより出力層が認識実装から
疎結合になり、将来 VLM 等へ差し替えても出力層は無改修で済みます。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np


@dataclass
class Frame:
    """カメラから取得した 1 フレーム（OpenCV BGR 画像）."""
    image: np.ndarray


@dataclass
class RecognitionResult:
    """認識層の出力."""
    # 人物ごとのセグメンテーションマスク（float 配列。値が大きいほど人物らしい）
    masks: List[np.ndarray] = field(default_factory=list)
    # 検出人数
    person_count: int = 0
    # 33 点ランドマーク（将来の VLM / 姿勢解析用に保持）
    landmarks: list = field(default_factory=list)
