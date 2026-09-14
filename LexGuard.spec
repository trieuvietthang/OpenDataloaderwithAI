# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

# opendataloader_pdf bundles a ~24MB Java CLI jar as package data (accessed at
# runtime via importlib.resources) — PyInstaller's static analysis only picks
# up Python source, so the jar must be collected explicitly or "Standard" PDF
# extraction silently fails on a machine that isn't the dev machine.
datas = [('logo.png', '.')] + collect_data_files('opendataloader_pdf')

# Docling is a deliberately optional, on-demand dependency (see IS_FROZEN in
# openloader.py — the portable build tells users to run from source for it
# instead of bundling it). If it happens to be pip-installed on the machine
# doing the build (e.g. for local testing), PyInstaller's static analysis
# still finds the `from docling... import ...` statements in openloader.py
# and pulls in the whole stack — torch alone is ~370MB. Exclude it and its
# exclusive dependency tree explicitly so the portable build stays small
# regardless of what's installed on the build machine.
DOCLING_ECOSYSTEM_EXCLUDES = [
    'docling', 'docling_core', 'docling_parse', 'docling_ibm_models',
    'torch', 'torchvision', 'transformers', 'onnxruntime', 'tokenizers',
    'safetensors', 'accelerate', 'huggingface_hub', 'hf_xet',
    'cv2', 'opencv-python', 'scipy', 'pandas', 'grpc',
]

a = Analysis(
    ['openloader.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'fitz', 'pikepdf', 'pytesseract', 'PIL', 'mammoth', 'markdownify', 'markdown', 'opendataloader_pdf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=DOCLING_ECOSYSTEM_EXCLUDES,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LexGuard',
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
    icon=['logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LexGuard',
)
