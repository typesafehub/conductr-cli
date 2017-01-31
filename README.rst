|build_status| |latest_version|

Command Line Interface (CLI) for Lightbend ConductR
---------------------------------------------------

Installation
~~~~~~~~~~~~

There are two types of installation:

* "native" where we have pre-built a native package for Windows, Linux and OS X requiring no other dependencies; and
* "python" where you must install Python 3 and use pip3 to install it.

Install natively
^^^^^^^^^^^^^^^^

Lightbend hosts native images at bintray: https://bintray.com/lightbend/generic/conductr-cli. Download an archive that is suitable for your environment and then place the resultant package in a place accessible from your PATH. For example, on Unix, copy the contents of archive to your /usr/local/bin folder.

Install using Python
^^^^^^^^^^^^^^^^^^^^

Install the ``conductr-cli`` with ``pip3``. Depending on your OS the command is:

**macOS**

.. code:: bash

    pip3 install conductr-cli

**Linux**

Install the ``conductr-cli`` package as you have installed other pip3 package. To install the package for all users, use:

.. code:: bash

    sudo pip3 install conductr-cli

To install it only for the current user, use:

.. code:: bash

    pip3 install --user conductr-cli

**Windows**

.. code:: bash

    pip install conductr-cli

Upgrade using pip3
^^^^^^^^^^^^^^^^^^

The ``conductr-cli`` can be updated by using the pip3 ``-U`` option:

**macOS**

.. code:: bash

    pip3 install -U conductr-cli

**Linux**

Install the ``conductr-cli`` package as you have installed other pip3 package. To install the package for all users, use:

.. code:: bash

    sudo pip3 install -U conductr-cli

To install it only for the current user, use:

.. code:: bash

    pip3 install --user -U conductr-cli

**Windows**

.. code:: bash

    pip install -U conductr-cli

Setup Bintray credentials
^^^^^^^^^^^^^^^^^^^^^^^^^

Bundles and ConductR images are hosted on Bintray. Please ensure that your Bintray credentials that have access to the Lightbend repositories are located at: ``.lightbend/commercial.credentials``.

How to get a Bintray account that has access to the Lightbend repositories is described at: http://developers.lightbend.com/docs/reactive-platform/2.0/setup/setup-sbt.html


CLI Usage
~~~~~~~~~

sandbox
^^^^^^^

Execute ``sandbox`` with any of the supported sub-commands or options,
e.g.

.. code:: bash

    $ sandbox -h
    usage: sandbox [-h] {version,run,stop} ...

To start a ConductR sandbox cluster with 3 nodes and the `visualization` feature run:

.. code:: bash

    sandbox run <CONDUCTR_VERSION> --nr-of-instances 3 --feature visualization

Pick up the latest ConductR version from https://www.lightbend.com/product/conductr/developer

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
                  {version,info,service-names,acls,load,run,stop,unload,events,logs,setup-dcos} 
                  ...

Most sub-commands connect to a ConductR instance and therefore you have to specify its IP and port. This can be done in different ways. You can specify the IP via the ``--host`` option and the port via the ``--port`` option. Alternatively, you can set the environment variables ``CONDUCTR_HOST`` and ``CONDUCTR_PORT``. Default values will be used if both are not set. The port defaults to 9005. By default, the IP address will be automatically resolved to the sandbox host IP.

Here’s an example for loading a bundle:

.. code:: bash

    conduct load sbt-conductr-tester-1.0.0-e172570d3c0fb11f4f9dbb8de519df58dcb490799f525bab43757f291e1d104d.zip

Note that when specifying IPV6 addresses then you must surround them with square brackets e.g.:

.. code:: bash

    conduct info --host [fe80:0000:0000:0000:0cb3:e2ff:fe74:902d]

To enable HTTP Basic Authentication, provide the following settings file in the ``~/.conductr/settings.conf``.

.. code::

    conductr {
      auth {
        enabled  = true
        username = "steve"
        password = "letmein"
      }
      server_ssl_verification_file = "/home/user/validate-server.pem"
    }

When the switch ``enabled`` is set to ``true``, HTTP Basic Authentication is enabled. Set to ``false`` to disable.
 Set the ``username`` and ``password`` accordingly. The ``server_ssl_verification_file`` points to an absolute path of the file used to validate the SSL cert of the server.

It's important to note the CLI will fail with an error if HTTP Basic Authentication is enabled without HTTPS.

shazar
^^^^^^

The ``shazar`` command can be used:

- for packaging a directory that has a structure of a bundle to a bundle archive;
- for packaging a bundle’s configuration to a bundle archive;

In both cases the source files are zipped and a SHA256 digest of the archive is appended to the bundle archive file name.

For pointers on command usage run ``shazar -h``.

Developers
~~~~~~~~~~

> Note that we presently package the dcos library as source. When https://github.com/dcos/dcos-cli/pull/823 becomes available then
we should remove this directory and depend on it directly.

For macOS, you should ensure firstly that you have the latest Xcode command line tools installed:

.. code:: bash

  xcode-select --install

Now, install the latest python3 version on your system, on macOS use:

.. code:: bash

  brew install python3

The tests executing the tests in multiple python versions. For all OS environments, pyenv is used to support multiple installations of python during testing. On macOS, use brew to install pyenv:

.. code:: bash

  brew install pyenv

Installation instructions for other OS can be found at https://github.com/yyuu/pyenv. With pyenv installed you can do things like ``pyenv local 3.4.3`` or ``pyenv local system``. Don't forget to update your login profile to setup pyenv (the doc describes how).

After pyenv has been installed, add python 3.4. On macOS use:

.. code:: bash

  CFLAGS="-I$(brew --prefix openssl)/include" \
  LDFLAGS="-L$(brew --prefix openssl)/lib" \
  pyenv install -v 3.4.3

For others OS this is easier:

.. code:: bash

  pyenv install -v 3.4.3

Make sure to install the ``tox`` module for multi-environment testing:

.. code:: bash

  pip3 install tox

Afterwards, install the necessary dependencies for each environment and to set the python versions for ``conductr-cli``:

.. code:: bash

  pip3 install .
  pyenv local system 3.4.3

Running
^^^^^^^

If you want to run ``conduct`` or ``sandbox`` locally, i.e. without installation, ``cd`` into the project directory and execute:

.. code:: bash

    pip3 install -e .
    conduct
    sandbox

Tests
^^^^^

Execute the following command to run unit tests for the current version of python3:

.. code:: bash

    python3 -m unittest

Execute the following command to run all defined tests:

.. code:: bash

    tox

Releasing
^^^^^^^^^

CLI releases to the pip3 repository can be performed completely from the GitHub project page. Follow these steps to cut a release:

1. Edit `conductr_cli/__init__.py <conductr_cli/__init__.py>`_ file to contain the version to be released.
2. Create a new release on the `Github releases page <https://github.com/typesafehub/conductr-cli/releases>`_.

After CI build is finished for the tagged commit, new version will automatically be deployed to PyPi repository.

**Native**

Pyinstaller is required. Please visit http://www.pyinstaller.org/ to obtain instructions on how to install it.

To build native packages follow the form:

.. code:: bash

    pyinstaller --onefile conductr_cli/conduct.py
    pyinstaller --onefile conductr_cli/shazar.py
    pyinstaller --hidden-import psutil --onefile conductr_cli/sandbox.py
    
This will result in standalone images for your current environment being created in a `dist` folder.


.. |build_status| image:: https://travis-ci.org/typesafehub/conductr-cli.svg?branch=master
    :target: https://travis-ci.org/typesafehub/conductr-cli
    :alt: Build status of the master branch

.. |latest_version| image:: https://img.shields.io/pypi/v/conductr-cli.svg?label=latest%20version
    :target: https://pypi.python.org/pypi/conductr-cli
    :alt: Latest version released on PyPi
