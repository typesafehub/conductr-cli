import os
from setuptools import setup, find_packages
from conductr_cli import __version__

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='conductr-cli',
    version=__version__,
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'conduct = conductr_cli.conduct:run',
            'shazar = conductr_cli.shazar:run',
        ],
    },

    install_requires=[
        'requests>=2.3.0',
        'argcomplete>=0.8.1',
        'pyhocon==0.2.1'
    ],
    test_suite='conductr_cli.test',

    license='Apache 2',
    description='A CLI client for Typesafe ConductR',
    url='https://github.com/typesafehub/conductr-cli',
)
