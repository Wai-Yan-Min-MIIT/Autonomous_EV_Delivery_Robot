# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['alpha_tech_app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\L-72\\Wai_yan_folder\\programming\\Autonomous_ev_delivery_car\\programs\\ev_delivery_app\\static', 'static'), ('C:\\Users\\L-72\\Wai_yan_folder\\programming\\Autonomous_ev_delivery_car\\programs\\ev_delivery_app\\data', 'data')],
    hiddenimports=[],
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
    name='alpha_tech_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\L-72\\Wai_yan_folder\\programming\\Autonomous_ev_delivery_car\\programs\\ev_delivery_app\\static\\MIC_Logo.ico'],
)
