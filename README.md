## Command Line Interface (CLI) for Typesafe ConductR

### Installation

You have to install the following software:

- Python 3, e.g. via `brew install python3`

#### Install as a pip package

1. Build a pip package.

  ``` bash
  python3 setup.py sdist
  ```

2. Install built package to the current user (make sure to have `~/.local/bin` in your PATH):

  ``` bash
  pip3 install --user dist/typesafe-conductr-cli-0.1.tar.gz
  ```

  Or install built package to all users:

  ``` bash
  pip3 install dist/typesafe-conductr-cli-0.1.tar.gz
  ```

#### Install as a deb package

1. Build a docker image for building a deb package:

  ``` bash
  docker build -t debian-distribution deb_dist/
  ```

2. Run built docker image:

  ``` bash
  docker run -v $(pwd):/source debian-distribution
  ```

3. Install built deb package:

  ``` bash
  dpkg -i deb_dist/python3-typesafe-conductr-cli_0.1-1_all.deb
  ```

4. Install required dependencies:

  ``` bash
  apt-get install -f
  ```

#### Autocomplete support

If you have installed argcomplete and want to activate Bash completion for the CLI,
you have to execute the following, either transiently in your terminal session or more permanently in your
`.bashrc` or `.bash_profile`:

``` bash
eval "$(register-python-argcomplete conduct)"
```

Alternatively, if you have a Bash version 4.2 or later, you can activate global completion once:

``` bash
activate-global-python-argcomplete --dest=/path/to/bash_completion.d
```

### Running tests

Execute the following command to run all defined tests:

``` bash
python3 -m unittest discover
```

### CLI Usage

#### conduct

Execute `conduct` with any of the supported sub-commands or options, e.g.

``` bash
$ conduct -h
usage: conduct [-h] {version,info,load,run,stop,unload} ...

optional arguments:
-h, --help            show this help message and exit

subcommands:
valid subcommands

{version,info,load,run,stop,unload}
help for subcommands
version             print version information
info                get information about one or all bundles
load                load a bundle
run                 run a bundle
stop                stop a abundle
unload              unload a bundle
```

Most sub-commands connect to a ConductR instance and therefore you have to specify its host and port;
if not given, $HOSTNAME or "127.0.0.1" will be used for the host and 9005 for the port. You can specify
the host via the `--host` option and the port via the `--port` option or use the `CONDUCTR_PORT` environment
variable.

Here's an example for loading a bundle:

``` bash
conduct load \
--nr-of-cpus 2 \
--memory 104857600 \
--disk-space 104857600 \
--roles web-server \
-- test-lib/src/main/resources/sbt-typesafe-conductr-tester-1.0.0-e172570d3c0fb11f4f9dbb8de519df58dcb490799f525bab43757f291e1d104d.tgz
```

Notice that in this example it's neessary to separate the bundle from the values of the `--roles` option with `--`,
else the bundle would be treated as another role and hence the bundle itself would be missing.

In other cases, e.g. if there are no roles given or if the bundle doesn't come directly after the roles,
this is not needed, like in the following example where an additional configuration is loaded:

``` bash
conduct load \
--nr-of-cpus 2 \
--memory 104857600 \
--disk-space 104857600 \
test-lib/src/main/resources/sbt-typesafe-conductr-tester-1.0.0-e172570d3c0fb11f4f9dbb8de519df58dcb490799f525bab43757f291e1d104d.tgz \
test-lib/src/main/resources/configuration-d928496f2c561332621efd3663b9e13ca7608948983f44c9b9cf273b2036e155.tgz
```

If you want to use an external ConductR host, you can use the `--host` and `--port` properties which default
to `$HOSTNAME` or "127.0.0.1" and "9005" respectively, e.g.:

``` bash
conduct load \
--host $DOCKER_HOST_IP
...
```

#### shatar

The `shatar` command can be used:

* for packaging a directory that has a structure of a bundle to a bundle archive;
* for packaging a bundle's configuration to a bundle archive;

In both cases source files are tarred and gzipped and SHA256 digest of the archive
is appended to the bundle archive file name.

For pointers on command usage run `shatar -h`.
