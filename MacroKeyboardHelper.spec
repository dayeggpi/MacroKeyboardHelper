# MacroKeyboardHelper.spec
# Generate with: pyinstaller MacroKeyboardHelper.spec

block_cipher = None

a = Analysis(
    ['MacroKeyboardHelper.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'), 
        ('prev.png', '.'), 
        ('next.png', '.'), 
        ('close.png', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MacroKeyboardHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico'
)