"""出力層: 副次出力ハンドラの抽象基底.

配信そのものは共有バッファ経由で行われますが、それとは別に
「フレームをどう扱うか（破棄するか／将来サーバへ転送・保存するか）」を
差し替えられるようにするための拡張点です。

Phase 1 では NullOutputHandler（破棄）を使用します。
Phase 2 で ServerTransferHandler を追加する場合は、この OutputHandlerBase を
実装するだけで出力層に差し込めます。転送/保存を有効化する前には
法務確認をゲートにする運用とします（要件 R-02）。
"""

from __future__ import annotations

import abc

import numpy as np

from ..types import RecognitionResult


class OutputHandlerBase(abc.ABC):
    @abc.abstractmethod
    def handle(self, annotated_image: np.ndarray, result: RecognitionResult) -> None:
        raise NotImplementedError


class NullOutputHandler(OutputHandlerBase):
    """Phase 1 の既定。保存も送信もしない（プライバシーバイデザイン）。"""

    def handle(self, annotated_image: np.ndarray, result: RecognitionResult) -> None:
        return None
