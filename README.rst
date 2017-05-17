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

If you use macOS and `brew` then you can quickly:

.. code:: bash
    
    brew install typesafehub/conductr/conductr-cli
    
Alternatively, Lightbend hosts native images at bintray: https://bintray.com/lightbend/generic/conductr-cli. Download an archive that is suitable for your environment and then place the resultant package in a place accessible from your PATH. For example, on Unix, copy the contents of archive to your /usr/local/bin folder.

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

By default, the sandbox is started with a number of default features: proxying, oci-in-docker, and lite-logging. These features can be disabled by providing the `--no-default-features` flag. Note that due to virtualization requirements, OCI-in-Docker is mandatory on macOS and thus cannot be disabled.

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

If HTTP Basic Authentication is enabled then the CLI will send HTTP requests using HTTPS instead of HTTP.

bndl
^^^^

The ``bndl`` command is used to create or modify bundles. It can be used for the following:

- Creating a bundle from Docker and OCI images
- Modifying a bundle's ``bundle.conf`` properties to add annotations, roles, etc.

To learn more, see ``bndl -h``.

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
  pyenv install -v 3.4.5
  pyenv install -v 3.5.2

For others OS this is easier:

.. code:: bash

  pyenv install -v 3.4.5
  pyenv install -v 3.5.2

Make sure to install the ``tox`` module for multi-environment testing:

.. code:: bash

  pip3 install tox

Afterwards, install the necessary dependencies for each environment, ensure that the ``.tox`` is not present and to set the python versions for ``conductr-cli``:

.. code:: bash

  pip3 install .
  rm -rf .tox
  pyenv local system 3.4.5 3.5.2

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

Python Compatibility
^^^^^^^^^^^^^^^^^^^^

ConductR CLI supports Python ``3.4`` and above.

When using standard or third-party libraries, always ensure the implementation is compatible with Python ``3.4``.

When browsing the latest Python 3 documentation or arriving to a documentation page from a search result, be sure to check the Python version of the documentation page.

When using a method, check if there's a mention of whether it has been introduced after Python ``3.4``.

Releasing
^^^^^^^^^

CLI releases to the pip3 repository can be performed completely from the GitHub project page. Follow these steps to cut a release:

1. Edit `conductr_cli/__init__.py <conductr_cli/__init__.py>`_ file to contain the version to be released.
2. Create a new release on the `Github releases page <https://github.com/typesafehub/conductr-cli/releases>`_.

After CI build is finished for the tagged commit, new version will automatically be deployed to PyPi repository.

**Native**

Ensure correct system requirement is used for each target platform.

For MacOS:

* OSX version ``10.11``: native executables built on ``10.11`` will be compatible with ``10.12``, but the reverse is not true.
* Python version ``3.5``.

For Linux:

* Ubuntu version ``14.04.5 LTS``.
* Python version ``3.4``.

For Windows:

* Windows 7
* Python version ``3.5``.
* 7Zip executable from http://www.7-zip.org/download.html required to build zip file on the command line. When installing 7Zip, ensure the 7z.exe is available on the Windows ``%PATH%``.

Pyinstaller version ``3.2.1`` or above is required. Please visit http://www.pyinstaller.org/ to obtain instructions on how to install it.

Ensure the native executables are built from tagged release commit.

Continue to build native packages.

For MacOS and Linux:

.. code:: bash

    sh package-native-zip.sh [release-version-number]


For Windows perform the following steps.

Open a DOS prompt, and then execute the following command.

.. code:: bash

    set CONDUCTR_HOST=192.168.10.1

For those using Windows VM, the local sandbox address ``192.168.10.1`` can be used - ensure the sandbox on the host machine has been started before proceeding further. This will allow the CLI on the Windows VM to connect to the ConductR running on the host machine.

If you wish to use ConductR running from a different host, replace ``192.168.10.1`` accordingly.

.. code:: bash

    package-native-zip.bat [release-version-number]


The ``package-native-zip.sh`` and ``package-native-zip.bat`` follow performs the following steps.

First it builds the native executables.

.. code:: bash

    pyinstaller --onefile conductr_cli/conduct.py
    pyinstaller --hidden-import psutil --onefile conductr_cli/sandbox.py    
    pyinstaller --onefile conductr_cli/shazar.py
    pyinstaller --onefile conductr_cli/bndl.py
    
This will result in standalone images for your current environment being created in a ``dist`` folder.

It will ensure correct versions are built. This is done by comparing the version number from the output of the commands below with the input to the script. If there's a mismatch, the script will exit with failure.

.. code:: bash

    ./dist/sandbox version
    ./dist/conduct version

For MacOS and Linux, perform sanity check by running:

.. code:: bash

    ./dist/sandbox run 2.0.0 -f visualization
    ./dist/conduct info
    ./dist/shazar -h
    ./dist/bndl -h    

For Windows, perform the following since the ``sandbox`` command is not supported:

.. code:: bash

    ./dist/conduct info
    ./dist/shazar -h
    ./dist/bndl -h    



.. |build_status| image:: https://travis-ci.org/typesafehub/conductr-cli.svg?branch=master
    :target: https://travis-ci.org/typesafehub/conductr-cli
    :alt: Build status of the master branch

.. |latest_version| image:: https://img.shields.io/pypi/v/conductr-cli.svg?label=latest%20version
    :target: https://pypi.python.org/pypi/conductr-cli
    :alt: Latest version released on PyPi
