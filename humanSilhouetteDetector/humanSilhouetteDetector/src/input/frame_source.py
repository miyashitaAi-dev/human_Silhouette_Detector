"""入力層: カメラ映像取得の抽象化.

基本設計の「FrameSource インターフェース契約」を実装します。
抽象基底 FrameSourceBase を介すことで、将来カメラを動画ファイルや
ネットワーク映像に差し替えても、認識層・出力層は無改修で済みます。
"""

from __future__ import annotations

import abc
from typing import Optional

import cv2

from ..types import Frame


class FrameSourceBase(abc.ABC):
    """フレーム供給源の契約（read / release）."""

    @abc.abstractmethod
    def read(self) -> Optional[Frame]:
        """1 フレーム返す。取得できなければ None。"""
        raise NotImplementedError

    @abc.abstractmethod
    def release(self) -> None:
        """リソースを解放する。"""
        raise NotImplementedError


class CameraOpenError(RuntimeError):
    """カメラを開けなかったときの例外。"""


class CameraFrameSource(FrameSourceBase):
    """OpenCV VideoCapture による Web カメラ実装。"""

    def __init__(self, camera_index: int, width: int, height: int) -> None:
        self._cap = cv2.VideoCapture(camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self._cap.isOpened():
            raise CameraOpenError(f"カメラを開けません (index={camera_index})")

    def read(self) -> Optional[Frame]:
        ok, image = self._cap.read()
        if not ok or image is None:
            return None
        return Frame(image=image)

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
