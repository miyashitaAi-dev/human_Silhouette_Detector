"""認識層: MediaPipe Pose Landmarker 実装.

詳細設計「(c) Recognizer」に対応します。
実行モードは VIDEO（同期）です（変更管理票 CR-02）。背景スレッドが
1 フレームずつ同期的に処理する設計に整合し、実装が単純で堅牢になります。

出力の masks は MediaPipe の型ではなく素の numpy 配列に変換して返し、
出力層を MediaPipe 非依存に保ちます。
"""

from __future__ import annotations

from typing import List

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from ..types import Frame, RecognitionResult
from .base import RecognizerBase


class MediaPipePoseRecognizer(RecognizerBase):
    """Pose Landmarker による人物検出 + 輪郭マスク + 人数算出。"""

    def __init__(
        self,
        model_path: str,
        num_poses: int,
        min_detection_confidence: float,
        output_segmentation_masks: bool,
    ) -> None:
        options = mp_vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=num_poses,
            min_pose_detection_confidence=min_detection_confidence,
            output_segmentation_masks=output_segmentation_masks,
        )
        self._landmarker = mp_vision.PoseLandmarker.create_from_options(options)

    def recognize(self, frame: Frame, timestamp_ms: int) -> RecognitionResult:
        # OpenCV は BGR、MediaPipe は RGB を想定するため変換する。
        rgb = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # VIDEO モードはタイムスタンプ（ミリ秒・単調増加）が必須。
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        masks: List[np.ndarray] = []
        if result.segmentation_masks:
            for m in result.segmentation_masks:
                # mp.Image -> numpy(float32) へ。配列はコピーして保持する。
                masks.append(np.array(m.numpy_view(), copy=True))

        landmarks = result.pose_landmarks or []
        return RecognitionResult(
            masks=masks,
            person_count=len(landmarks),
            landmarks=landmarks,
        )

    def close(self) -> None:
        self._landmarker.close()
