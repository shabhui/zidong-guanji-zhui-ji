# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

app_dir = Path(SPECPATH)
qml_dir = app_dir / "qml"

hiddenimports = []
hiddenimports += collect_submodules("PySide6.QtQml")
hiddenimports += collect_submodules("PySide6.QtQuick")
hiddenimports += collect_submodules("PySide6.QtQuickControls2")
hiddenimports += [
    "controller",
    "settings_service",
    "network_service",
    "power_service",
    "script_service",
]

qml_datas = [(str(qml_dir), "qml")]

a = Analysis(
    [str(app_dir / "main.py")],
    pathex=[str(app_dir)],
    binaries=[],
    datas=qml_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoShutdownQt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AutoShutdownQt-2.0",
)
