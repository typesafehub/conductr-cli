import sys


def sys_meipass():
    """
    A safe way to obtain sys._MEIPASS by performing a check whether `frozen` attribute in the `sys` is present and has
    the value of True.
    :return: sys._MEIPASS if ran within PyInstaller, else None
    """
    return sys._MEIPASS if getattr(sys, 'frozen', False) else None
