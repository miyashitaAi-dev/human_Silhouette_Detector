# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import os

# mediapipe は内部で動的ロードを多用するため collect_all で全収集
mp_datas, mp_binaries, mp_hiddenimports = collect_all('mediapipe')

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=mp_binaries,
    datas=[
        ('templates', 'templates'),       # Jinja2 テンプレート
        ('static', 'static'),             # CSS 等の静的ファイル
        ('models', 'models'),             # MediaPipe モデル (.task)
        *mp_datas,
    ],
    hiddenimports=[
        *mp_hiddenimports,
        'cv2',
        'flask',
        'werkzeug',
        'jinja2',
        'click',
        'itsdangerous',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HumanSilhouetteDetector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # 起動時にコンソールを表示（デバッグ用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HumanSilhouetteDetector',
)
