# -*- mode: python ; coding: utf-8 -*-
import ffpyplayer
FFPYPLAYER_PATH = ffpyplayer.__path__[0]

block_cipher = None


a = Analysis(
    ['src/main.py'],
    pathex=['.', './src', './venv/Lib/site-packages'],
    binaries=[
        (f'{FFPYPLAYER_PATH}/*.pyd', 'ffpyplayer'),
        (f'{FFPYPLAYER_PATH}/player/*.pyd', 'ffpyplayer/player'),
    ],
    datas=[('statics', 'statics')],
    hiddenimports=[
        'ffpyplayer.threading',
        'ffpyplayer.player.queue',
        'ffpyplayer.player.frame_queue',
        'ffpyplayer.player.decoder',
        'ffpyplayer.player.clock',
        'ffpyplayer.player.core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Tyler',
    icon='statics/tile-icon.ico',
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
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in ffpyplayer.dep_bins],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Tyler',
)
app = BUNDLE(
    coll,
    name='Tyler.app',
    icon='statics/tile-icon.ico',
    bundle_identifier=None,
)
