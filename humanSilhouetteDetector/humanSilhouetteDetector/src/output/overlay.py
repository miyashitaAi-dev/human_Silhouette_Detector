"""出力層: 輪郭重畳描画.

詳細設計「(d) draw_overlay」に対応する、顧客指定の品質ライン実装です。
人物マスクを統合・二値化し、輪郭を抽出して元映像へ半透明塗り + 輪郭線で
重畳します。MediaPipe には依存せず numpy / OpenCV のみで完結します。
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..types import RecognitionResult


def _build_binary_mask(result: RecognitionResult, height: int, width: int,
                       threshold: float) -> Optional[np.ndarray]:
    """全人物マスクを統合し、二値（0/255）の uint8 マスクを返す。"""
    if not result.masks:
        return None
    combined = None
    for mask in result.masks:
        # マスク解像度がフレームと異なる場合に備えてリサイズする。
        if mask.shape[:2] != (height, width):
            mask = cv2.resize(mask, (width, height))
        combined = mask if combined is None else np.maximum(combined, mask)
    binary = (combined > threshold).astype(np.uint8) * 255
    return binary


def draw_overlay(image_bgr: np.ndarray, result: RecognitionResult, config,
                 fps: Optional[float] = None) -> np.ndarray:
    """元フレームに人物輪郭と情報を重畳した新しい画像を返す。"""
    canvas = image_bgr.copy()
    h, w = canvas.shape[:2]

    binary = _build_binary_mask(result, h, w, config.mask_threshold)
    if binary is not None:
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if contours:
            # 1) 半透明の塗り
            overlay = canvas.copy()
            cv2.drawContours(overlay, contours, -1, config.outline_color, thickness=cv2.FILLED)
            canvas = cv2.addWeighted(
                overlay, config.fill_alpha, canvas, 1.0 - config.fill_alpha, 0
            )
            # 2) 輪郭線
            cv2.drawContours(
                canvas, contours, -1, config.outline_color, thickness=config.outline_thickness
            )

    # 3) 情報表示（人数・FPS）
    if config.show_person_count:
        _put_text(canvas, f"People: {result.person_count}", (10, 30))
    if fps is not None:
        _put_text(canvas, f"FPS: {fps:.1f}", (10, 60))

    return canvas


def _put_text(image: np.ndarray, text: str, org: tuple) -> None:
    """視認性のため黒縁取り付きで文字を描画する。"""
    cv2.putText(image, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(image, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)


def make_placeholder(width: int, height: int, message: str) -> np.ndarray:
    """カメラ未接続時などに表示する代替フレームを生成する。"""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:] = (40, 40, 40)
    size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
    org = ((width - size[0]) // 2, (height + size[1]) // 2)
    _put_text(image, message, org)
    return image
