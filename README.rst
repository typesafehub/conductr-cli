|build_status| |latest_version|

Command Line Interface (CLI) for Typesafe ConductR
--------------------------------------------------

Installation
~~~~~~~~~~~~

Python 3 is required. For OS X users use ``brew install python3``.

Install using pip
^^^^^^^^^^^^^^^^^

You may either install or upgrade to all users:

.. code:: bash

    sudo pip3 install conductr-cli

(use -U with the above if you need to upgrade)

... or, and if you’re not using brew (there’s a problem with user installs as of the time writing this), install to the current user (make sure to have ``~/.local/bin`` in your PATH):

.. code:: bash

    pip3 install -U --user conductr-cli

Install as a deb package
^^^^^^^^^^^^^^^^^^^^^^^^

Build a docker image for building a deb package:

.. code:: bash

    docker build -t debian-distribution deb_dist/

Run built docker image:

.. code:: bash

  docker run -v $(pwd):/source debian-distribution

Install built deb package:

.. code:: bash

    dpkg -i deb_dist/python3-conductr-cli_0.1-1_all.deb

Install required dependencies:

.. code:: bash

    apt-get install -f

Autocomplete support
^^^^^^^^^^^^^^^^^^^^

If you have installed argcomplete and want to activate Bash completion for the CLI, you have to execute the following, either transiently in your terminal session or more permanently in your ``.bashrc`` or ``.bash_profile``:

.. code:: bash

    eval "$(register-python-argcomplete conduct)"

Alternatively, if you have a Bash version 4.2 or later, you can activate global completion once:

.. code:: bash

    activate-global-python-argcomplete --dest=/path/to/bash_completion.d

If you are running zsh, execute the following command to enable autocomplete:

.. code:: bash

    autoload bashcompinit && autoload compinit && bashcompinit && compinit && eval "$(register-python-argcomplete conduct)"

CLI Usage
~~~~~~~~~

sandbox
^^^^^^^

Execute ``sandbox`` with any of the supported sub-commands or options,
e.g.

.. code:: bash

    $ sandbox -h
    usage: sandbox [-h] {run,debug,stop} ...

    optional arguments:
      -h, --help            show this help message and exit

    commands:
      {run,debug,stop}      Use one of the following sub commands
        run                 Run ConductR sandbox cluster
        debug               Not supported. Use `sbt-conductr-sandbox` instead
        stop                Stop ConductR sandbox cluster

The sandbox is connecting to the running Docker VM to start the ConductR nodes inside Docker containers. The host IP address of the Docker VM is automatically resolved by using either `docker-machine` or `boot2docker`. If none of the Docker commands exist then the IP address is resolved with the command `hostname` or as the last fallback the IP address ``127.0.0.1`` is used. It is also possible to skip this automatic resolving of the Docker host IP by setting the environment variable ``CONDUCTR_IP`` which will be then used instead.

  In order to use the following features you should ensure that the machine that runs Docker has enough memory, typically at least 2GB. VM configurations such as those provided via docker-machine and Oracle's VirtualBox can be configured like so:

.. code:: bash

        docker-machine stop default
        VBoxManage modifyvm default --memory 2048
        docker-machine start default

To start a ConductR sandbox cluster with 3 nodes and the `visualization` feature run:

.. code:: bash

    sandbox run 1.1.9 --nr-of-containers 3 --feature visualization

To stop this cluster run:

.. code:: bash

    sandbox stop

conduct
^^^^^^^

Execute ``conduct`` with any of the supported sub-commands or options,
e.g.

.. code:: bash

    $ conduct -h
    usage: conduct [-h]
                  {version,info,services,load,run,stop,unload,events,logs} ...

    optional arguments:
      -h, --help            show this help message and exit

    commands:
      {version,info,services,load,run,stop,unload,events,logs}
                            Use one of the following sub commands
        version             print version
        info                print bundle information
        services            print service information
        load                load a bundle
        run                 run a bundle
        stop                stop a bundle
        unload              unload a bundle
        events              show bundle events
        logs                show bundle logs

Most sub-commands connect to a ConductR instance and therefore you have to specify its IP and port. This can be done in different ways. You can specify the IP via the ``--ip`` option and the port via the ``--port`` option. Alternatively, you can set the environment variables ``CONDUCTR_IP`` and ``CONDUCTR_PORT``. Default values will be used if both are not set. The port defaults to 9005. The IP address will be automatically resolved to the Docker host IP by using either `docker-machine` or `boot2docker`. If none of the Docker commands exist then the IP address is resolved with the command `hostname` or as the last fallback the IP address ``127.0.0.1`` is used.

The commands provided via CLI uses version 1.0 of the ConductR API by default. When working with version 1.1 of ConductR, set the ``CONDUCTR_API_VERSION`` environment variable to ``1.1``. Alternatively you can specify the API version via the ``--api-version`` option.

Here’s an example for loading a bundle:

.. code:: bash

    conduct load sbt-conductr-tester-1.0.0-e172570d3c0fb11f4f9dbb8de519df58dcb490799f525bab43757f291e1d104d.zip

Note that when specifying IPV6 addresses then you must surround them with square brackets e.g.:

.. code:: bash

    conduct info --ip [fe80:0000:0000:0000:0cb3:e2ff:fe74:902d]

shazar
^^^^^^

The ``shazar`` command can be used:

- for packaging a directory that has a structure of a bundle to a bundle archive;
- for packaging a bundle’s configuration to a bundle archive;

In both cases the source files are zipped and a SHA256 digest of the archive is appended to the bundle archive file name.

For pointers on command usage run ``shazar -h``.

Developers
~~~~~~~~~~

For OS X, you should ensure firstly that you have the latest Xcode command line tools installed.

Now install the latest python3 version on your system, on OS X use:

.. code:: bash

  brew install python3

The tests executing the tests in multiple python versions. For all OS environments, pyenv is used to support multiple installations of python during testing. Refer to https://github.com/yyuu/pyenv for information on how to install pyenv. With pyenv installed you can do things like ``pyenv local 3.4.3`` or ``pyenv local system``. Don't forget to update your login profile to setup pyenv (the doc describes how).

Then for OS X, install python 3.4:

.. code:: bash

  CFLAGS="-I$(brew --prefix openssl)/include" \
  LDFLAGS="-L$(brew --prefix openssl)/lib" \
  pyenv install -v 3.4.3

For others this is easier:

.. code:: bash

  pyenv install -v 3.4.3

Make sure to install the ``virtualenv`` module for python3:

.. code:: bash

  pip3 install virtualenv

Also, make sure to install the necessary dependencies for each environment and to set the python versions for ``conductr-cli``:

.. code:: bash

  pip3 install -e .
  pyenv local system 3.4.3

Be sure to install flake for testing:

.. code:: bash

  pip3 install flake8

Running
^^^^^^^

If you want to run ``conduct`` or ``sandbox`` locally, i.e. without installation, ``cd`` into the project directory and execute:

.. code:: bash

    python3 -m conductr_cli.conduct
    python3 -m conductr_cli.sandbox

Tests
^^^^^

Execute the following command to run unit tests for the current version of python3:

.. code:: bash

    python3 -m unittest

Execute the following command to run all defined tests:

.. code:: bash

    python3 setup.py test

To run only a specific test case in a test suite:

.. code:: bash

    python3 setup.py test -a "-- -s conductr_cli.test.test_conduct_unload:TestConductUnloadCommand.test_failure_invalid_address"

Releasing
^^^^^^^^^

CLI releases can be performed completely from the GitHub project page. Follow these steps to cut a release:

1. Edit `conductr_cli/__init__.py <conductr_cli/__init__.py>`_ file to contain the version to be released.
2. Create a new release on the `Github releases page <https://github.com/typesafehub/conductr-cli/releases>`_.

After CI build is finished for the tagged commit, new version will automatically be deployed to PyPi repository.



.. |build_status| image:: https://travis-ci.org/typesafehub/conductr-cli.svg?branch=master
    :target: https://travis-ci.org/typesafehub/conductr-cli
    :alt: Build status of the master branch

.. |latest_version| image:: https://img.shields.io/pypi/v/conductr-cli.svg?label=latest%20version
    :target: https://pypi.python.org/pypi/conductr-cli
    :alt: Latest version released on PyPi
