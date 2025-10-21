# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['menuestilizado.py'],
    pathex=[],
    binaries=[],
    # MUDANÇA: Adicione suas pastas de ícones e conversores aqui
    datas=[
        ('icons', 'icons'), 
        ('conversores', 'conversores')
    ],
    # MUDANÇA: Adicione módulos que podem ser difíceis de encontrar
    hiddenimports=[
        'PyPDF2',
        'camelot',
        'cv2',
        'unidecode',
        'PIL',
        'pdfplumber',
        'numpy.linalg'
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
    a.binaries,
    a.datas,
    name='Conversor Bancario', # MUDANÇA: Um nome mais descritivo para o .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    # MUDANÇA: Garante que a janela do console não apareça
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # MUDANÇA: Adicione um ícone ao seu executável!
    icon='icons\convert.ico' 
)