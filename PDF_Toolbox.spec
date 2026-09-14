# -*- mode: python ; coding: utf-8 -*-
# PDF_Toolbox.spec — PyInstaller build specification for OpenSource PDF Toolbox

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ── Collect tkinterdnd2 (includes native tkdnd .dll files) ───────────────────
tkdnd2_datas, tkdnd2_binaries, tkdnd2_hiddenimports = collect_all('tkinterdnd2')

# ── Collect PyMuPDF (fitz) data files ────────────────────────────────────────
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all('fitz')

# ── Collect pikepdf data files ────────────────────────────────────────────────
pikepdf_datas, pikepdf_binaries, pikepdf_hiddenimports = collect_all('pikepdf')

# ── Application assets ────────────────────────────────────────────────────────
app_datas = [
    ('assets', 'assets'),
]

a = Analysis(
    ['pdf_tool_main.py'],
    pathex=['.'],
    binaries=fitz_binaries + pikepdf_binaries + tkdnd2_binaries,
    datas=app_datas + tkdnd2_datas + fitz_datas + pikepdf_datas,
    hiddenimports=[
        'tkinterdnd2',
        'tkinterdnd2.TkinterDnD',
        'fitz',
        'pikepdf',
        'pikepdf._cpphelpers',
        'pikepdf._version',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageOps',
        'PIL.ImageFilter',
    ] + tkdnd2_hiddenimports + fitz_hiddenimports + pikepdf_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'tensorflow', 'torch', 'boto3', 'botocore',
        'sqlalchemy', 'sqlmap', 'flask', 'django',
        'IPython', 'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OpenSource PDF Toolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # windowed mode — no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\icon.ico',
)
