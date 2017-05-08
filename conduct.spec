# -*- mode: python -*-

from PyInstaller.compat import is_darwin
import os


if is_darwin:
    # Include Python's cacert file as part of the packaged native executable.
    # This is because in OSX the OpenSSL from Macports and Homebrew doesn't fallback to CA certs stored in OSX keychain
    # tool.
    # The workaround is based on this PyInstaller recipe:
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OpenSSL-Certificate
    #
    # and its corresponding PR:
    # https://github.com/pyinstaller/pyinstaller/pull/1411/files
    #
    # This workaround relies on setting SSL_CERT_FILE environment variable, and this environment variable is applicable
    # on Python 3.4 and 3.5: https://bugs.python.org/issue22449
    #
    # Some further info on how OSX OpenSSL cert validation:
    # https://hynek.me/articles/apple-openssl-verification-surprises/
    #
    import ssl
    cert_datas = [(ssl.get_default_verify_paths().cafile, 'lib')]
else:
    cert_datas = []

block_cipher = None


a = Analysis(['conductr_cli/conduct.py'],
             pathex=[os.path.abspath(os.getcwd())],
             binaries=[],
             datas=cert_datas,
             hiddenimports=[],
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
          name='conduct',
          debug=False,
          strip=False,
          upx=True,
          console=True )
