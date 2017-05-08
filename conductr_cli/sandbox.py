from conductr_cli import main_handler
import sys
import os


if getattr(sys, 'frozen', False):
    # Assume Python's cacert file is included as part of the packaged native executable.
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
    os.environ['SSL_CERT_FILE'] = os.path.join(sys._MEIPASS, 'lib', 'cert.pem')


def main_method():
    from conductr_cli import sandbox_main
    sandbox_main.run()


def run():
    main_handler.run(main_method)


if __name__ == '__main__':
    run()
