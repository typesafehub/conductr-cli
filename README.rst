|Build Status| |Latest Version|

Command Line Interface (CLI) for Typesafe ConductR
--------------------------------------------------

Installation
~~~~~~~~~~~~

Python 3 is required. For OS X users use ``brew install python3``.

Install using pip
^^^^^^^^^^^^^^^^^

You may either install to all users:

.. code:: bash

    sudo pip3 install typesafe-conductr-cli

... or, and if you’re not using brew (there’s a problem with user installs as of the time writing this), install to the current user (make sure to have ``~/.local/bin`` in your PATH):

.. code:: bash

    pip3 install --user typesafe-conductr-cli

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

    dpkg -i deb_dist/python3-typesafe-conductr-cli_0.1-1_all.deb

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

Running tests
~~~~~~~~~~~~~

Execute the following command to run all defined tests:

.. code:: bash

    python3 setup.py test

Releasing
~~~~~~~~~

CLI releases can be performed completely from the GitHub project page. Follow these steps to cut a release:

1. Edit `typesafe_conductr_cli/__init__.py`_ file to contain the version to be released.
2. Create a new release in GitHub `releases page`_.

After CI build is finished for the tagged commit, new version will automatically be deployed to PyPi repository.

CLI Usage
~~~~~~~~~

conduct
^^^^^^^

Execute ``conduct`` with any of the supported sub-commands or options,
e.g.

.. code:: bash

    $ conduct -h
    usage: conduct [-h] {version,info,services,load,run,stop,unload} ...

    optional arguments:
      -h, --help            show this help message and exit

    subcommands:
      valid subcommands

      {version,info,services,load,run,stop,unload}
                            help for subcommands
        version             print version
        info                print bundle information
        services            print service information
        load                load a bundle
        run                 run a bundle
        stop                stop a bundle
        unload              unload a bundle

Most sub-commands connect to a ConductR instance and therefore you have to specify its IP and port; if not given, ``CONDUCTR_IP`` environment variable or ``127.0.0.1`` will be used for the IP and ``CONDUCTR_PORT`` or ``9005`` for the port. Alternatively you can specify the IP via the ``--ip`` option and the port via the ``--port`` option.

Here’s an example for loading a bundle:

.. code:: bash

    conduct load sbt-typesafe-conductr-tester-1.0.0-e172570d3c0fb11f4f9dbb8de519df58dcb490799f525bab43757f291e1d104d.zip

shazar
^^^^^^

The ``shazar`` command can be used:

- for packaging a directory that has a structure of a bundle to a bundle archive;
- for packaging a bundle’s configuration to a bundle archive;

In both cases the source files are zipped and a SHA256 digest of the archive is appended to the bundle archive file name.

For pointers on command usage run ``shazar -h``.

.. |Build Status| image:: https://travis-ci.org/typesafehub/typesafe-conductr-cli.png
    :target: https://travis-ci.org/typesafehub/typesafe-conductr-cli
    :alt: Build Status
.. |Latest Version| image:: https://pypip.in/version/typesafe-conductr-cli/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/typesafe-conductr-cli/
    :alt: Latest Version
.. _releases page: https://github.com/typesafehub/typesafe-conductr-cli/releases/new
.. _typesafe_conductr_cli/__init__.py: https://github.com/typesafehub/typesafe-conductr-cli/blob/master/typesafe_conductr_cli/__init__.py
