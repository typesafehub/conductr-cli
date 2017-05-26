from conductr_cli import main_handler
import certifi
import sys
import os


if getattr(sys, 'frozen', False):
    # Use cacert provided by the certifi package when running as native executable.
    #
    # This is to normalize the different ways cacert is being packaged across different platform.
    #
    # Note on OSX
    # -----------
    # In OSX the OpenSSL from Macports and Homebrew doesn't fallback to CA certs stored in OSX keychain tool.
    #
    # Some further info on how OSX OpenSSL cert validation:
    # https://hynek.me/articles/apple-openssl-verification-surprises/
    #
    # Note on Linux
    # -----------
    # Also in various flavours of Linux, the cacert is packaged differently.
    #
    # In Ubuntu it's installed under /etc/ssl/certs containing various .pem files each from different Root CA.
    #
    # In RHEL/Centos, it's installed under /etc/ssl/certs/ca-bundle.crt
    #
    # This solution relies on setting SSL_CERT_FILE environment variable, and this environment variable is applicable
    # on Python 3.4 and 3.5: https://bugs.python.org/issue22449
    #
    os.environ['SSL_CERT_FILE'] = os.path.join(certifi.where())


def main_method():
    from conductr_cli import conduct_main
    conduct_main.run()


def run():
    main_handler.run(main_method)


if __name__ == '__main__':
    run()
