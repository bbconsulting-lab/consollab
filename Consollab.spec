# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

block_cipher = None

streamlit_datas = collect_data_files('streamlit')
streamlit_metadata = copy_metadata('streamlit')
packaging_metadata = copy_metadata('packaging')
requests_metadata = copy_metadata('requests')

a = Analysis(
    ['splash_app.py'],
    pathex=[],
    binaries=[],
    datas=[('streamlit_app.py', '.'), ('ConsolLab_logo.png', '.')] + streamlit_datas + streamlit_metadata + packaging_metadata + requests_metadata,
    hiddenimports=[
        'streamlit',
        'streamlit.runtime.scriptrunner.magic_funcs', 
        'streamlit.runtime.scriptrunner.magic',
        'requests',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
        'pandas',
        'numpy',
        'altair',
        'pyarrow',
        'tenacity',
        'rich',
        'click',
        'tornado',
        'pydeck',
        'watchdog',
        'blinker',
        'cachetools',
        'webview',
        'webview.platforms.winforms',
    ],
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
    name='Consollab',
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
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ConsolLab',
)