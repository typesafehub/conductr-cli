import json
import logging
import sys
import urllib
import arrow
import os

from pyhocon.exceptions import ConfigException
from requests import status_codes
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
from urllib.error import URLError
from zipfile import BadZipFile
from conductr_cli import terminal, docker_machine
from conductr_cli.exceptions import DockerMachineError, Boot2DockerError, MalformedBundleError, BundleResolutionError, \
    WaitTimeoutError, InsecureFilePermissions
from subprocess import CalledProcessError


# FileNotFoundError is only available on > python 3.3
NOT_FOUND_ERROR = getattr(__builtins__, 'FileNotFoundError', OSError)


def connection_error(log, err, args):
    log.error('Unable to contact ConductR.')
    log.error('Reason: {}'.format(err.args[0]))
    if args.local_connection:
        log.error('Start the ConductR sandbox with: sandbox run IMAGE_VERSION')
    else:
        log.error('Make sure it can be accessed at {}'.format(err.request.url))


def pretty_json(s):
    s_json = json.loads(s)
    return json.dumps(s_json, sort_keys=True, indent=2, separators=(',', ': '))


def handle_connection_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as err:
            log = get_logger_for_func(func)
            connection_error(log, err, *args)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_http_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as err:
            log = get_logger_for_func(func)
            log.error('{} {}'.format(err.response.status_code, err.response.reason))
            if err.response.text != '':
                log.error(err.response.text)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_invalid_config(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigException as err:
            log = get_logger_for_func(func)
            log.error('Unable to parse bundle.conf.')
            log.error('{}.'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_no_file(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except urllib.error.HTTPError as err:
            log = get_logger_for_func(func)
            log.error('Resource not found: {}'.format(err.url))
            return False
        except URLError as err:
            log = get_logger_for_func(func)
            log.error('File not found: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bad_zip(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadZipFile as err:
            log = get_logger_for_func(func)
            log.error('Problem with the bundle: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_malformed_bundle(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MalformedBundleError as err:
            log = get_logger_for_func(func)
            log.error('Problem with the bundle: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bundle_resolution_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BundleResolutionError as err:
            log = get_logger_for_func(func)
            log.error('Bundle not found: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_wait_timeout_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WaitTimeoutError as err:
            log = get_logger_for_func(func)
            log.error('Timed out: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_conduct_load_read_timeout_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ReadTimeout as err:
            log = get_logger_for_func(func)
            log.error('Timed out waiting for response from the server: {}'.format(err.args[0]))
            log.error('One possible issue may be that there are not enough resources or machines with the roles '
                      'that your bundle requires')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_insecure_file_permissions(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InsecureFilePermissions as err:
            log = get_logger_for_func(func)
            log.error('File permissions are not secure: {}'.format(err.args[0]))
            log.error('Please choose a file where only the owner has access, e.g. 700')
            return False

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
    vm_name = docker_machine.vm_name()

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DockerMachineError:
            log = get_logger_for_func(func)
            log.error('Docker VM has not been started.')
            log.error('Use the following command to start the VM:')
            log.error('  docker-machine start {}'.format(vm_name))
        except Boot2DockerError:
            log = get_logger_for_func(func)
            log.error('Docker VM has not been started.')
            log.error('Use the following command to start the VM:')
            log.error('  boot2docker up')

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_docker_errors(func):
    log = get_logger_for_func(func)
    vm_name = docker_machine.vm_name()

    def handle_linux():
        log.error('The docker service has not been started.')
        log.error('To start the docker service run:')
        log.error('  sudo service docker start')

    def handle_non_linux(*args, **kwargs):
        log.info('Docker could not connect to the docker VM.')
        log.info('It looks like the docker environment variables are not set. Let me try to set them..')
        [set_env(env[0], env[1]) for env in resolve_envs()]
        try:
            terminal.docker_ps()
            log.info('The Docker environment variables have been set for this command.')
            log.info('Continue processing..')
            log.warning('To set the environment variables for each terminal session '
                        'follow the instructions of the command:')
            log.warning('  docker-machine env {}'.format(vm_name))
            log.info('')
            return func(*args, **kwargs)
        except CalledProcessError:
            log.error('Docker could not be configured automatically.')
            log.error('Please set the docker environment variables.')

    def resolve_envs():
        try:
            env_lines = terminal.docker_machine_env(vm_name)
            log.info('Retrieved docker environment variables with `docker-machine env {}`'.format(vm_name))
        except NOT_FOUND_ERROR:
            try:
                env_lines = terminal.boot2docker_shellinit()
                log.info('Retrieved docker environment variables with: boot2docker shellinit')
                log.warning('boot2docker is deprecated. Upgrade to docker-machine.')
            except NOT_FOUND_ERROR:
                return []
        return [resolve_env(line) for line in env_lines if line.startswith('export')]

    def resolve_env(line):
        key = line.partition(' ')[-1].partition('=')[0]
        value = line.partition(' ')[-1].partition('=')[2].strip('"')
        return key, value

    def set_env(key, value):
        log.info('Set environment variable: {}="{}"'.format(key, value))
        os.environ[key] = value

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CalledProcessError:
            if sys.platform == 'linux' or sys.platform == 'linux2':
                return handle_linux()
            else:
                return handle_non_linux(*args, **kwargs)

        except NOT_FOUND_ERROR:
            log.error('docker command has not been found.')
            log.error('The sandbox need Docker to run the ConductR nodes in virtual containers.')
            log.error('Please install Docker first: https://www.docker.com')

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


def get_logger_for_func(func):
    return logging.getLogger('conductr_cli.{}'.format(func.__name__))
