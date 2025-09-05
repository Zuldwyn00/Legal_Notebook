# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# Collect tiktoken data files
tiktoken_datas = collect_data_files('tiktoken')

a = Analysis(
    ['ui\\app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('prompts.yaml', '.'),
        ('config.yaml', '.'),
        ('.env', '.'),
        ('scripts\\clients\\client_configs.json', 'scripts\\clients\\'),
        ('scripts\\data\\jsons\\processed_files.json', 'scripts\\data\\jsons\\'),
        ('scripts\\data\\pdfs\\', 'scripts\\data\\pdfs\\'),
    ] + tiktoken_datas,
    hiddenimports=[
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        'tiktoken_ext.openai_public.cl100k_base',
        'tiktoken_ext.openai_public.o200k_base',
        'tiktoken_ext.openai_public.p50k_base',
        'tiktoken_ext.openai_public.r50k_base',
        'tiktoken.registry',
        'tiktoken.load',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
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
    name='Legal_Notebook_Program',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='l.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Legal_Notebook_Program',
)
