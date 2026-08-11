# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('../frontend/dist', 'frontend/dist'), ('migrations', 'migrations'), ('ingredient_rules.json', '.'), ('meal_name_fixes.json', '.'), ('nutrition_rules.json', '.'), ('backup.json', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'ultralytics', 'xformers', 'accelerate', 'kokoro', 'optimum', 'pandas', 'scipy', 'matplotlib', 'pyarrow', 'pydantic', 'pydantic_core', '_pytest', 'pytest', 'aiohttp', 'fsspec', 'watchdog', 'fonttools', 'hyperframe', 'h2', 'hpack', 'multidict', 'yarl', 'aiosignal'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
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
)
