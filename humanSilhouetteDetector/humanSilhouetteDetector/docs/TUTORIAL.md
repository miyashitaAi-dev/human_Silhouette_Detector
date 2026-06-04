# コードリーディング解説

本ドキュメントはプロジェクト作成者向けの学習用解説です。
ソースコードを8つの区切りに分けて、設計の意図・使われた技術・「なぜそう書いたか」を説明します。

---

## 第1回：プロジェクト全体の設計思想

### このアプリが何をするか

```
Webカメラ → 人物検出 → シルエット描画 → ブラウザに配信
```

### 3層アーキテクチャ

```
┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Input層    │ →  │  Recognition層   │ →  │  Output層        │
│  カメラから  │    │  人物を検出して   │    │  描画結果を       │
│  画像を取得  │    │  マスクを生成     │    │  どう扱うか       │
└─────────────┘    └──────────────────┘    └──────────────────┘
```

各層は**抽象基底クラス（インターフェース）**で定義されています。

| 層 | 抽象クラス | 実装クラス |
|---|---|---|
| Input | `FrameSourceBase` | `CameraFrameSource`（OpenCV） |
| Recognition | `RecognizerBase` | `MediaPipePoseRecognizer` |
| Output | `OutputHandlerBase` | `NullOutputHandler`（何もしない） |

**なぜこうするか：** 将来「カメラ → 動画ファイル」に変えたくなっても、Input層だけ差し替えればよく、他の層は一切触らない。

### スレッド構造（生産者・消費者パターン）

```
[背景スレッド：生産者]              [Flaskスレッド：消費者]
camera_worker.py が担当             app.py が担当

カメラ取得
  ↓
人物認識（重い処理）                 ブラウザから /video_feed にアクセス
  ↓                                        ↓
シルエット描画                      最新JPEGを取り出してブラウザへ送る
  ↓
JPEGに変換
  ↓
共有バッファに保存 ←── Lock ──→ 共有バッファから読み出し
```

認識処理（重い）と配信（速さが必要）を分離することで、どちらかが遅くなっても互いをブロックしません。

---

## 第2回：設定とデータ構造 `config.py` / `src/types.py`

### `config.py` — アプリ全体の設定

```python
@dataclass
class Config:
    camera_index: int = 0
    frame_width: int = 640
    ...

config = Config()  # シングルトン：アプリ全体で共有
```

**`@dataclass` を使う理由：** `__init__` を自動生成してくれるため、全パラメータ分の代入を手書きしなくて済む。

**`config = Config()` をファイル末尾に置く理由：** どこからでも `from config import config` で同じインスタンスを参照できる（シングルトンパターン）。

### `src/types.py` — データの入れ物

```python
@dataclass
class RecognitionResult:
    masks: List[np.ndarray] = field(default_factory=list)
    person_count: int = 0
    landmarks: list = field(default_factory=list)
```

**なぜ専用の型を作るか：** MediaPipe 固有の型を使い回すと、将来 MediaPipe をやめたとき全ファイルを修正することになる。`RecognitionResult` を挟むことで認識層だけを差し替えれば済む設計になる。

**`field(default_factory=list)` の理由：**
```python
# NG：インスタンス間でリストを共有してしまう（Python の落とし穴）
masks: list = []

# OK：インスタンスごとに新しいリストを作る
masks: List[np.ndarray] = field(default_factory=list)
```

---

## 第3回：Input層 `src/input/frame_source.py`

```python
class FrameSourceBase(abc.ABC):
    @abc.abstractmethod
    def read(self) -> Optional[Frame]: ...

    @abc.abstractmethod
    def release(self) -> None: ...
```

**`@abc.abstractmethod` の効果：** このメソッドを実装しないサブクラスはインスタンス化でエラーになる。「このメソッドは必ず実装せよ」という契約。

**将来の拡張イメージ：**
```python
class FileFrameSource(FrameSourceBase):    # 動画ファイルを読む
    def read(self): ...
    def release(self): ...

class NetworkFrameSource(FrameSourceBase): # IPカメラを読む
    def read(self): ...
    def release(self): ...
```

`CameraWorker` は `FrameSourceBase` 型として受け取るので、どの実装に替えてもコード変更なし。

---

## 第4回：Recognition層 `src/recognition/`

### 動作モードの選択

MediaPipe には3つの動作モードがある：

| モード | 仕組み | 向いている用途 |
|---|---|---|
| `IMAGE` | 1枚ずつ完全に独立 | 静止画処理 |
| `VIDEO` | タイムスタンプで同期処理 | **このプロジェクト** |
| `LIVE_STREAM` | 非同期・コールバック方式 | 複雑なイベント駆動 |

`VIDEO` モードにした理由：背景スレッドが「処理して → 結果を待って → 次へ」と**順番に処理する**設計に一番合っているから。

### `recognize()` の流れ

```python
def recognize(self, frame: Frame, timestamp_ms: int) -> RecognitionResult:
    # ① BGR → RGB に変換（OpenCV は BGR、MediaPipe は RGB）
    rgb = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # ② 認識実行
    result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

    # ③ マスクを numpy 配列にコピー（内部メモリへの参照を避けるため）
    masks = []
    for m in result.segmentation_masks:
        masks.append(np.array(m.numpy_view(), copy=True))  # copy=True が重要

    return RecognitionResult(masks=masks, ...)
```

**`copy=True` が必要な理由：** `numpy_view()` はMediaPipe内部メモリへの参照を返す。次フレーム処理で上書きされると参照先データも変わってしまうため、独立したコピーを作る。

---

## 第5回：Output層 `src/output/`

### `base.py` — NullOutputHandler の意図

```python
class NullOutputHandler(OutputHandlerBase):
    def handle(self, annotated_image, result) -> None:
        return None  # 何もしない
```

「何もしない」クラスを明示的に作る理由：
1. **プライバシーバイデザイン** — 映像を保存・送信しないことをコードで表明する
2. **将来の差し替えポイント** — Phase2でサーバ転送したければここに実装を追加するだけ

### `overlay.py` — 描画の3ステップ

```
マスク（float配列）→ 二値化 → 輪郭抽出 → 半透明塗り＋輪郭線
```

**ステップ1：マスクの二値化**
```python
combined = np.maximum(combined, mask)           # 複数人を合成
binary = (combined > threshold).astype(np.uint8) * 255  # 白黒に変換
```

マスクはもともと `0.0〜1.0` の float 配列（「どれだけ人物らしいか」の確率）。輪郭検出できる形にするため白黒2値に変換する。

**ステップ2：半透明ブレンド**
```python
overlay = canvas.copy()
cv2.drawContours(overlay, contours, -1, color, thickness=cv2.FILLED)
canvas = cv2.addWeighted(overlay, 0.3, canvas, 0.7, 0)
# 結果 = 塗り済み画像 × 0.3 + 元画像 × 0.7
```

**ステップ3：縁取り文字**
```python
cv2.putText(image, text, org, font, 0.7, (0,0,0), thickness=4)  # 黒で太く（縁）
cv2.putText(image, text, org, font, 0.7, (255,255,255), thickness=1)  # 白で細く上書き
```

同じ座標に2回描くことで、どんな背景色でも読める縁取り文字になる。

---

## 第6回：生産者スレッド `src/camera_worker.py`

### daemon スレッド

```python
self._thread = threading.Thread(target=self._run, daemon=True)
```

`daemon=True` の意味：メインプロセス（Flask）が終了すると自動で道連れに終了する。`daemon=False` だとメインが終了してもスレッドが生き残りプロセスが終わらない。

### Lock による排他制御

```python
# 書く側（生産者）
with self._lock:
    self._latest_jpeg = jpeg.tobytes()

# 読む側（消費者）
with self._lock:
    return self._latest_jpeg
```

`with self._lock:` ブロックは同時に1つしか入れないドア。Lock なしで同時アクセスすると、書き途中の壊れたデータを読む**競合状態**が起きる。

### FPS の指数移動平均

```python
inst = 1.0 / dt                              # 瞬間FPS
self._fps = self._fps * 0.9 + inst * 0.1    # 前回90% + 今回10%
```

瞬間値をそのまま表示すると数値がガタガタする。直近の値を少しずつ反映することでなめらかな表示になる。

### 例外をフレーム単位でスキップ

```python
try:
    result = recognizer.recognize(frame, timestamp_ms)
    annotated = draw_overlay(...)
except Exception:
    annotated = frame.image  # 認識失敗 → 生映像をそのまま表示
```

1フレームの認識に失敗してもアプリ全体は止まらず、生映像を流し続ける。

---

## 第7回：配信サーバ `app.py` とフロントエンド

### MJPEG ストリーミングの仕組み

通常のHTTPは「リクエスト1回 → レスポンス1回」で終わりだが、MJPEGは接続を切らずに画像を送り続ける。

```
ブラウザ          Flask
  │──── GET /video_feed ────→│
  │←── --frame ──────────────│   yield JPEG1
  │←── --frame ──────────────│   yield JPEG2
  │←── --frame ──────────────│   yield JPEG3 ...（接続が続く限り）
```

ブラウザ側は `<img src="/video_feed">` の1行だけで受け取れる。

### `yield` でレスポンスを少しずつ送る

```python
def _mjpeg_generator():
    while True:
        jpeg = worker.get_latest()
        yield boundary + jpeg_data   # ← 値を返しながら一時停止
        time.sleep(1.0 / 30.0)
```

`return` は終了するが `yield` は一時停止して再開できる（ジェネレータ）。Flaskは `yield` が返すたびにブラウザへ送信する。

### CSS の主要テクニック

**CSS変数で色を一元管理：**
```css
:root { --live: #4ade80; --accent: #ffc857; }
```

**点滅アニメーション：**
```css
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
.dot { animation: pulse 1.6s ease-in-out infinite; }
```

**疑似要素で四隅レチクル（HTMLに要素追加不要）：**
```css
.reticle::before { top: 0; left: 0; border-right: none; border-bottom: none; }
.reticle::after  { bottom: 0; right: 0; border-left: none; border-top: none; }
```

---

## 第8回：まとめと学習ポイント

### 設計判断の「なぜ」まとめ

| 判断 | 理由 |
|---|---|
| 抽象基底クラスを使う | 将来の差し替えコストを最小にするため |
| 生産者・消費者パターン | 重い処理と速さが必要な処理を分離するため |
| MediaPipe の VIDEO モード | 同期的に1フレームずつ処理する設計に合うため |
| NullOutputHandler を作る | プライバシーバイデザインをコードで表現するため |
| MJPEG を選ぶ | WebSocket より実装がシンプルで `<img>` タグ1行で受け取れるため |

### 拡張ポイント

```
【入力を変える】
  CameraFrameSource → FileFrameSource（動画ファイル）
  → FrameSourceBase を実装するだけ

【認識を変える】
  MediaPipeRecognizer → VLMRecognizer（画像説明AI）
  → RecognizerBase を実装するだけ（ライセンス確認要）

【出力を変える】
  NullOutputHandler → ServerTransferHandler（サーバ保存）
  → OutputHandlerBase を実装するだけ（法務確認要）
```

どの拡張も**他の層を一切触らない**ことが、この設計の価値。

### 使われた技術・概念の一覧

| 区分 | 概念 | どこで使った |
|---|---|---|
| **設計** | 3層アーキテクチャ | Input / Recognition / Output の分離 |
| **設計** | 生産者・消費者パターン | CameraWorker ↔ Flask |
| **設計** | シングルトン | `config = Config()` |
| **Python** | `@dataclass` | `Config`, `Frame`, `RecognitionResult` |
| **Python** | 抽象基底クラス（ABC） | 各層の `Base` クラス |
| **Python** | ジェネレータ（`yield`） | `_mjpeg_generator()` |
| **Python** | スレッド / Lock | `threading.Thread`, `threading.Lock` |
| **Python** | 例外処理 | カメラ未接続・認識失敗のスキップ |
| **OpenCV** | カメラ取得・輪郭抽出・画像合成・JPEGエンコード | 各所 |
| **MediaPipe** | Pose Landmarker | 人物検出 + セグメンテーション |
| **Flask** | ルーティング・テンプレート・ストリーミング | `app.py` |
| **CSS** | 変数・アニメーション・疑似要素 | `style.css` |
