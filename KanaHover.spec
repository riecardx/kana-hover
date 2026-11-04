# -*- mode: python ; coding: utf-8 -*-
"""KanaHover 0.7.1 portable Windows folder build; package is NOT launched."""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve()
VENDOR = ROOT / 'vendor' / 'python'
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(VENDOR / 'win32'))
sys.path.insert(0, str(VENDOR / 'win32' / 'lib'))
sys.path.insert(0, str(VENDOR / 'pywin32_system32'))
from version import DIST_NAME

datas = [
    (str(ROOT / 'tessdata'), 'tessdata'),
    (str(ROOT / 'vendor' / 'tesseract'), 'vendor/tesseract'),
]
binaries = []
hiddenimports = [
    'win32api', 'win32con', 'win32gui', 'win32process',
    'win32clipboard', 'pythoncom', 'pywintypes', 'psutil',
    'comtypes', 'comtypes.client', 'comtypes.gen',
    'pystray._win32', 'pystray._base', 'keyboard', 'pytesseract',
    'numpy', 'pydantic', 'PIL.ImageTk',
]
# Include entire Japanese lexicon, voice assets, compiled extension modules.
for package in ('sudachidict_core', 'sudachipy', 'pyopenjtalk'):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[
        str(ROOT),
        str(VENDOR),
        str(VENDOR / 'win32'),
        str(VENDOR / 'win32' / 'lib'),
        str(VENDOR / 'pywin32_system32'),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=list(dict.fromkeys(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'torch', 'tensorflow', 'onnxruntime', 'scipy', 'pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='KanaHover',
    console=False,
    disable_windowed_traceback=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=DIST_NAME,
)
