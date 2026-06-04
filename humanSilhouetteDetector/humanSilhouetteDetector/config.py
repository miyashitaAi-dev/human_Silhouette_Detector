"""アプリケーション設定.

詳細設計書 v0.1 の「config 具体値」を反映した初期値です。
値はテスト工程（工程⑤）で実機計測のうえ調整する前提です。
色は OpenCV の BGR 順である点に注意してください。
"""

from dataclasses import dataclass, field


@dataclass
class Config:
    # --- カメラ / 入力 ---
    camera_index: int = 0          # 既定カメラ
    frame_width: int = 640         # CPU 性能基準。重ければ下げる
    frame_height: int = 480

    # --- 認識モデル (MediaPipe Pose Landmarker) ---
    # 軽量版モデル。models/README.md の手順で取得して配置する。
    model_path: str = "models/pose_landmarker_lite.task"
    num_poses: int = 2                       # 控えめな初期値（お任せ確定）
    min_pose_detection_confidence: float = 0.5
    output_segmentation_masks: bool = True   # 輪郭抽出に必須

    # --- 描画 / 出力 ---
    mask_threshold: float = 0.5              # マスク二値化のしきい値
    fill_alpha: float = 0.3                  # 半透明塗りの不透明度
    outline_color: tuple = (0, 200, 255)     # 輪郭線の色 (BGR) = アンバー
    outline_thickness: int = 2
    show_person_count: bool = True           # 人数表示の ON/OFF（お任せ確定）

    # --- 配信 ---
    jpeg_quality: int = 80                   # 画質と帯域の妥協点
    host: str = "0.0.0.0"
    port: int = 5000


# アプリ全体で共有する単一インスタンス
config = Config()
