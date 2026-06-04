"""Flask アプリ本体（配信＝消費者）.

詳細設計「(e) Flask app.py」に対応します。
MJPEG ストリーミング（multipart/x-mixed-replace）で、背景スレッドが保持する
最新フレームをブラウザへ連続配信します。ブラウザは <img> タグで受けるだけです。
"""

from __future__ import annotations

import time

from flask import Flask, Response, render_template

from config import config
from src.camera_worker import CameraWorker

app = Flask(__name__)

# 起動時に背景スレッド（生産者）を開始する。
worker = CameraWorker()
worker.start()


def _mjpeg_generator():
    """最新 JPEG を multipart 形式で yield し続ける。"""
    boundary = b"--frame\r\n"
    while True:
        jpeg = worker.get_latest()
        if jpeg is None:
            time.sleep(0.03)
            continue
        yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
        # 過剰な送出を抑え CPU を空ける（約 30fps 上限）。
        time.sleep(1.0 / 30.0)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        _mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


if __name__ == "__main__":
    # threaded=True で配信と背景処理を並行させる。
    app.run(host=config.host, port=config.port, threaded=True, debug=False)
