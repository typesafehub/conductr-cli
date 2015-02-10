import os
from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='typesafe-conductr-cli',
    version='0.2',
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'conduct = typesafe_conductr_cli.conduct:run',
            'shazar = typesafe_conductr_cli.shazar:run',
        ],
    },

    install_requires=['requests>=2.3.0', 'argcomplete>=0.8.1'],
    test_suite='typesafe_conductr_cli.test',

    license='Apache 2',
    description='A CLI client for Typesafe ConductR',
    url='https://github.com/typesafehub/typesafe-conductr-cli',
)
