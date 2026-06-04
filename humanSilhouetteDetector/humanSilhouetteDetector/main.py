"""ローカルウィンドウ表示ランナー（任意の補助手段）.

Web 配信（app.py）が主たる提供形態ですが、開発時の動作確認用に
ローカルウィンドウへ直接表示する経路も用意しておきます。
'q' キーで終了します。
"""

from __future__ import annotations

import time

import cv2

from config import config
from src.input.frame_source import CameraFrameSource, CameraOpenError
from src.recognition.mediapipe_recognizer import MediaPipePoseRecognizer
from src.output.overlay import draw_overlay


def main() -> None:
    try:
        source = CameraFrameSource(config.camera_index, config.frame_width, config.frame_height)
    except CameraOpenError as exc:
        print(f"[ERROR] {exc}")
        return

    recognizer = MediaPipePoseRecognizer(
        model_path=config.model_path,
        num_poses=config.num_poses,
        min_detection_confidence=config.min_pose_detection_confidence,
        output_segmentation_masks=config.output_segmentation_masks,
    )

    start_ts = time.monotonic()
    prev = time.monotonic()
    fps = 0.0
    try:
        while True:
            frame = source.read()
            if frame is None:
                continue
            ts_ms = int((time.monotonic() - start_ts) * 1000)
            result = recognizer.recognize(frame, ts_ms)
            annotated = draw_overlay(frame.image, result, config, fps=fps)

            cv2.imshow("Human Silhouette Detector", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            now = time.monotonic()
            dt = now - prev
            prev = now
            if dt > 0:
                inst = 1.0 / dt
                fps = inst if fps == 0 else (fps * 0.9 + inst * 0.1)
    finally:
        source.release()
        recognizer.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
