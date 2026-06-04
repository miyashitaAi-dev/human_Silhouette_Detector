"""認識層: 認識器の抽象基底.

基本設計の「Recognizer インターフェース契約」です。
将来 VLM を併用する場合（Phase 2）も、この RecognizerBase を実装した
クラスを追加するだけで認識層に差し込めます。これが拡張点の正体です。
"""

from __future__ import annotations

import abc

from ..types import Frame, RecognitionResult


class RecognizerBase(abc.ABC):
    """認識器の契約。"""

    @abc.abstractmethod
    def recognize(self, frame: Frame, timestamp_ms: int) -> RecognitionResult:
        """1 フレームを認識し RecognitionResult を返す。"""
        raise NotImplementedError

    def close(self) -> None:  # 既定は何もしない
        """モデルリソースを解放する（必要な実装のみ上書き）。"""
