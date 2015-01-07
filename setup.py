import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='typesafe-conductr-cli',
    version='0.1',
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'conduct = typesafe_conductr_cli.conduct:run',
            'shatar = typesafe_conductr_cli.shatar:run',
        ],
    },

    install_requires=['requests>=2.3.0', 'argcomplete>=0.8.1'],

    license='Apache 2',
    description='A CLI client for Typesafe ConductR',
    long_description=README,
    url='https://github.com/typesafehub/typesafe-conductr-cli',
)
