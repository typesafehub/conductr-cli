import json
import sys
import urllib
import arrow
import os

from pyhocon.exceptions import ConfigException
from requests import status_codes
from requests.exceptions import ConnectionError, HTTPError
from urllib.error import URLError
from zipfile import BadZipFile
from conductr_cli import terminal
from conductr_cli.ansi_colors import RED, YELLOW, UNDERLINE, ENDC
from conductr_cli.exceptions import DockerMachineError, Boot2DockerError, MalformedBundleError
from subprocess import CalledProcessError


def error(message, *objs):
    """print to stderr"""
    print('{}{}Error{}: {}'.format(RED, UNDERLINE, ENDC, message.format(*objs)), file=sys.stderr)


def warn(message, *objs):
    print('{}{}Warning{}: {}'.format(YELLOW, UNDERLINE, ENDC, message.format(*objs)), file=sys.stdout)


def connection_error(err, args):
    error('Unable to contact ConductR.')
    error('Reason: {}'.format(err.args[0]))
    if args.local_connection:
        error('Start the ConductR sandbox with: sandbox run IMAGE_VERSION')
    else:
        error('Make sure it can be accessed at {}'.format(err.request.url))


def pretty_json(s):
    s_json = json.loads(s)
    print(json.dumps(s_json, sort_keys=True, indent=2, separators=(',', ': ')))


def handle_connection_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as err:
            connection_error(err, *args)

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_http_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as err:
            error('{} {}', err.response.status_code, err.response.reason)
            if err.response.text != '':
                error(err.response.text)

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_invalid_config(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigException as err:
            error('Unable to parse bundle.conf.')
            error('{}.', err.args[0])

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_no_file(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except urllib.error.HTTPError as err:
            error('Resource not found: {}', err.url)
        except URLError as err:
            error('File not found: {}', err.args[0])

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bad_zip(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadZipFile as err:
            error('Problem with the bundle: {}', err.args[0])

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_malformed_bundle(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MalformedBundleError as err:
            error('Problem with the bundle: {}', err.args[0])

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def raise_for_status_inc_3xx(response):
    """
    raise status when status code is 3xx
    """

    response.raise_for_status()
    if response.status_code >= 300:
        raise HTTPError(status_codes._codes[response.status_code], response=response)  # FIXME: _codes is protected


def handle_docker_vm_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DockerMachineError:
            error('Docker VM has not been started.')
            error('Use the following command to start the VM:')
            error('  docker-machine start default')
        except Boot2DockerError:
            error('Docker VM has not been started.')
            error('Use the following command to start the VM:')
            error('  boot2docker up')

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_docker_errors(func):
    def handle_linux():
        error('The docker service has not been started.')
        error('To start the docker service run:')
        error('  sudo service docker start')

    def handle_non_linux(*args, **kwargs):
        print('Docker could not connect to the docker VM.')
        print('It looks like the docker environment variables are not set. Let me try to set them..')
        [set_env(env[0], env[1]) for env in resolve_envs()]
        try:
            terminal.docker_ps()
            print('The Docker environment variables have been set for this command.')
            print('Continue processing..')
            warn('To set the environment variables for each terminal session follow the instructions of the command:')
            warn('  docker-machine env default')
            print('')
            return func(*args, **kwargs)
        except CalledProcessError:
            error('Docker could not be configured automatically.')
            error('Please set the docker environment variables.')

    def resolve_envs():
        try:
            env_lines = terminal.docker_machine_env('default')
            print('Retrieved docker environment variables with `docker-machine env default`')
        except FileNotFoundError:
            try:
                env_lines = terminal.boot2docker_shellinit()
                print('Retrieved docker environment variables with: boot2docker shellinit')
                warn('boot2docker is deprecated. Upgrade to docker-machine.')
            except FileNotFoundError:
                return []
        return [resolve_env(line) for line in env_lines if line.startswith('export')]

    def resolve_env(line):
        key = line.partition(' ')[-1].partition('=')[0]
        value = line.partition(' ')[-1].partition('=')[2].strip('"')
        return key, value

    def set_env(key, value):
        print('Set environment variable: {}="{}"'.format(key, value))
        os.environ[key] = value

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CalledProcessError:
            if sys.platform == 'linux' or sys.platform == 'linux2':
                return handle_linux()
            else:
                return handle_non_linux(*args, **kwargs)

        except FileNotFoundError:
            error('docker command has not been found.')
            error('The sandbox need Docker to run the ConductR nodes in virtual containers.')
            error('Please install Docker first: https://www.docker.com')

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def format_timestamp(timestamp, args):
    date = arrow.get(timestamp)

    if args.date and args.utc:
        return date.to('UTC').strftime('%Y-%m-%dT%H:%M:%SZ')
    elif args.date:
        return date.to('local').strftime('%c')
    elif args.utc:
        return date.to('UTC').strftime('%H:%M:%SZ')
    else:
        return date.to('local').strftime('%X')
