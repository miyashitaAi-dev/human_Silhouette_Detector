"""背景スレッド（生産者）.

詳細設計「(b) CameraWorker」に対応します。生産者・消費者パターンの生産者側で、
カメラ取得 → 認識 → 描画 → JPEG 化 を繰り返し、最新の 1 枚だけを Lock で
保護した共有バッファに保持します。配信側（消費者）はこの最新フレームを読むだけ。

これにより重い認識処理と速い配信が分離され、映像が固まりません（リスク R-05 対応）。
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import cv2

from .config import config
from .input.frame_source import CameraFrameSource, CameraOpenError
from .recognition.mediapipe_recognizer import MediaPipePoseRecognizer
from .output.base import NullOutputHandler, OutputHandlerBase
from .output.overlay import draw_overlay, make_placeholder


class CameraWorker:
    def __init__(self, output_handler: Optional[OutputHandlerBase] = None) -> None:
        self._latest_jpeg: Optional[bytes] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._output_handler = output_handler or NullOutputHandler()
        self._fps = 0.0

    # --- スレッド制御 ---
    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, name="camera-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    # --- 消費者から呼ばれる読み出し ---
    def get_latest(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    # --- 内部ループ ---
    def _store(self, image) -> None:
        ok, jpeg = cv2.imencode(
            ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), config.jpeg_quality]
        )
        if ok:
            with self._lock:
                self._latest_jpeg = jpeg.tobytes()

    def _run(self) -> None:
        # カメラを開けない場合はプレースホルダを配信し続ける（致命的にしない）。
        try:
            source = CameraFrameSource(config.camera_index, config.frame_width, config.frame_height)
        except CameraOpenError:
            placeholder = make_placeholder(config.frame_width, config.frame_height, "Camera not available")
            while self._running:
                self._store(placeholder)
                time.sleep(0.5)
            return

        recognizer = MediaPipePoseRecognizer(
            model_path=config.model_path,
            num_poses=config.num_poses,
            min_detection_confidence=config.min_pose_detection_confidence,
            output_segmentation_masks=config.output_segmentation_masks,
        )
        start_ts = time.monotonic()
        prev = time.monotonic()
        try:
            while self._running:
                frame = source.read()
                if frame is None:
                    continue  # 取得失敗フレームはスキップ
                timestamp_ms = int((time.monotonic() - start_ts) * 1000)
                try:
                    result = recognizer.recognize(frame, timestamp_ms)
                    annotated = draw_overlay(frame.image, result, config, fps=self._fps)
                    self._output_handler.handle(annotated, result)
                except Exception:
                    # 認識中の例外はフレーム単位でスキップし、直前フレームを保持。
                    annotated = frame.image
                    result = None
                self._store(annotated)

                # FPS 計測（指数移動平均で滑らかに）
                now = time.monotonic()
                dt = now - prev
                prev = now
                if dt > 0:
                    inst = 1.0 / dt
                    self._fps = inst if self._fps == 0 else (self._fps * 0.9 + inst * 0.1)
        finally:
            source.release()
            recognizer.close()
