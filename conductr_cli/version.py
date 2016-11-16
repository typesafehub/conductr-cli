from conductr_cli import __version__
import logging


def supported_api_versions():
    return ['1', '2']


def version(args):
    """`conduct version` command"""
    log = logging.getLogger(__name__)
    log.screen(__version__)
    log.screen('Supported API version(s): {}'.format(', '.join(supported_api_versions())))
    return True
