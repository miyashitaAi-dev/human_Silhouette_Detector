# モデルファイルの配置

本アプリは MediaPipe Pose Landmarker の軽量モデル（`.task`）を使用します。
リポジトリにはモデル本体を含めていません（容量・ライセンス管理のため）。
以下のいずれかの方法で取得し、このディレクトリに `pose_landmarker_lite.task` として配置してください。

## 取得方法

MediaPipe 公式の Pose Landmarker モデル一覧ページから「Pose landmarker (lite)」を
ダウンロードし、`models/pose_landmarker_lite.task` に保存します。

参考: MediaPipe 公式ドキュメント「Pose landmark detection」の Models セクション。

ダウンロード後の想定パス:

```
models/pose_landmarker_lite.task
```

より高精度が必要な場合は full / heavy 版に差し替え可能です。その場合は
`config.py` の `model_path` を更新してください（精度と処理速度はトレードオフ）。
