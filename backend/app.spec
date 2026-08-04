# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('../frontend/dist', 'frontend/dist'), ('migrations', 'migrations')],
    # §4.1 modularization: explicitly pull in the refactored packages so the
    # single-file build never tree-shrinks them out (routes register themselves
    # here via blueprint imports, which PyInstaller's tracer normally follows).
    hiddenimports=[
        'config',
        'models',
        'utils',
        'routes',
        'routes.meals',
        'routes.menu',
        'routes.grocery',
        'routes.data',
        'services',
        'services.menu_service',
        'services.grocery_service',
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
