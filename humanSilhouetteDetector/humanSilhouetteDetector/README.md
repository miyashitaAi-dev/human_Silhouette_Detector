# Human Silhouette Detector

Web カメラ映像から人物を検出し、その輪郭（シルエット）をリアルタイムに重畳表示する
コンピュータビジョン アプリケーションです。認識処理はサーバ側で行い、Flask により
ブラウザへ MJPEG 配信します。

`animalCnnAdd`（CNN 動物分類器）の後継として、ライブ映像の CV 処理へ拡張したものです。

## 特徴
- 人物の検出 + 輪郭セグメンテーション（MediaPipe Pose Landmarker）
- Flask によるブラウザ配信（MJPEG ストリーミング）
- 映像は処理後に破棄（保存・送信なし／プライバシーバイデザイン）
- 依存はすべて商用組込可ライセンス（`THIRD_PARTY_LICENSES.md` 参照）

## アーキテクチャ
3 層の疎結合構成です。各層は抽象基底クラスで分離され、将来の拡張（VLM 併用、
サーバ転送/保存）を他層に影響なく差し込めます。

```
入力層 (FrameSourceBase)  →  認識層 (RecognizerBase)  →  出力層 (OutputHandlerBase)
   カメラ抽象化               MediaPipe 実装              表示 + 破棄 / 将来 転送
```

背景スレッド（生産者）が「取得 → 認識 → 描画 → JPEG 化」を行い、Lock 保護された
最新フレームを保持。Flask の配信ジェネレータ（消費者）がそれを読み出して配信します。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

モデルファイルを配置します（`models/README.md` 参照）:

```
models/pose_landmarker_lite.task
```

## 実行

Web 配信（主たる提供形態）:

```bash
python app.py
# ブラウザで http://localhost:5000 を開く
```

ローカルウィンドウ表示（開発時の補助。'q' で終了）:

```bash
python main.py
```

## 設定
`config.py` で解像度・検出最大人数・しきい値・JPEG 画質などを調整できます。
初期値は控えめに設定しており、実機での性能計測のうえ調整してください。

## ドキュメント
プロジェクトの設計・テスト・運用documentは `docs/` にあります。

- [docs/PROJECT_DESIGN.md](docs/PROJECT_DESIGN.md) — 要件定義〜テストの統合設計書
- [docs/TEST_PLAN.md](docs/TEST_PLAN.md) — テスト仕様書 兼 結果報告書
- [docs/OPERATIONS.md](docs/OPERATIONS.md) — 運用・保守ガイド
- [docs/PROJECT_CLOSEOUT.md](docs/PROJECT_CLOSEOUT.md) — プロジェクト総括

## ライセンス
依存物のライセンスは `THIRD_PARTY_LICENSES.md` を参照してください。
