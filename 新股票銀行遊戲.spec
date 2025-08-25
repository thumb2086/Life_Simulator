# -*- mode: python ; coding: utf-8 -*-

# --- 導入 PyInstaller 的輔助函式 ---
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# --- 主要分析區塊 ---
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # --- 關鍵修改 1：加入 matplotlib 的數據文件 ---
    datas=collect_data_files('matplotlib'),
    # --- 關鍵修改 2：加入可能遺漏的模組 ---
    hiddenimports=['matplotlib.backends.backend_tkagg', 'pandas'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- 執行檔設定區塊 ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    # --- 檔名設定 ---
    name='新股票銀行遊戲',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # <-- False 代表是 --windowed 模式
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='新股票銀行遊戲',
)