# -*- mode: python -*-

import os

# FIXME: Remove once we have PyInstaller 3.3
# Temporary workaround until PyInstaller's boto hook imports the correct method
# https://github.com/pyinstaller/pyinstaller/issues/2384
# Fix is scheduled for PyInstaller 3.3
from PyInstaller.utils.hooks import is_module_satisfies
import PyInstaller.compat
PyInstaller.compat.is_module_satisfies = is_module_satisfies


block_cipher = None


a = Analysis(['conductr_cli/sandbox.py'],
             pathex=[os.path.abspath(os.getcwd())],
             binaries=[],
             datas=[],
             hiddenimports=['configparser', 'psutil', 'semver', 'http'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sandbox',
          debug=False,
          strip=False,
          upx=True,
          console=True )
