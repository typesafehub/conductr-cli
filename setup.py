import os
import sys
from setuptools import setup, find_packages
from conductr_cli import __version__
from setuptools.command.test import test

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

install_requires = [
    'requests>=2.3.0',
    'argcomplete>=0.8.1',
    'pyhocon==0.2.1',
    'arrow>=0.6.0'
]
if sys.version_info[:2] == (3, 2):
    install_requires.extend([
        'pathlib==1.0.1',
        'mock==1.0.1'
    ])


class Tox(test):
    user_options = [('tox-args=', 'a', 'Arguments to pass to tox')]

    def __init__(self, dist, **kw):
        self.test_suite = True
        self.test_args = []
        self.tox_args = None
        super().__init__(dist, **kw)

    def initialize_options(self):
        test.initialize_options(self)

    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        else:
            args = []
        errno = tox.cmdline(args=args)
        sys.exit(errno)

setup(
    name='conductr-cli',
    version=__version__,
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'conduct = conductr_cli.conduct:run',
            'sandbox = conductr_cli.sandbox:run',
            'shazar = conductr_cli.shazar:run',
        ],
    },

    install_requires=install_requires,
    tests_require=['tox'],
    test_suite='conductr_cli.test',

    cmdclass={'test': Tox},

    license='Apache 2',
    description='A CLI client for Typesafe ConductR',
    url='https://github.com/typesafehub/conductr-cli',
)
