import sys


def is_linux():
    return sys.platform == 'linux' or sys.platform == 'linux2'
