# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for YouTube Notifier — one-file, no console window."""
from pathlib import Path

block_cipher = None

# client_secrets.json is NOT bundled into the exe. At runtime the frozen app reads
# it from %APPDATA%\YouTubeNotifier\ (see get_client_secrets_path() in utils/constants.py).
_datas = [
    ("i18n", "i18n"),
    ("resources", "resources"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        # keyring Windows backend (not auto-detected by PyInstaller)
        "keyring.backends.Windows",
        "keyring.backends.fail",
        "keyring.core",
        # Google auth / API client
        "google.auth.transport.requests",
        "google.oauth2.credentials",
        "google_auth_oauthlib.flow",
        "googleapiclient.discovery",
        "googleapiclient._helpers",
        # PyQt6 core modules
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        # Windows toast notifications
        "winotify",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "pytest_qt",
        "responses",
        "coverage",
        "tkinter",
        "_tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_icon = "resources/icon.ico" if Path("resources/icon.ico").exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="YouTubeNotifier",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
    version="file_version_info.txt",
)
