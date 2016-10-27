import json
import logging
import urllib
import arrow

from pyhocon.exceptions import ConfigException
from requests import status_codes
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
from urllib.error import URLError
from zipfile import BadZipFile
from conductr_cli import terminal, docker_machine
from conductr_cli.exceptions import AmbiguousDockerVmError, DockerMachineNotRunningError, \
    DockerMachineCannotConnectToDockerError, MalformedBundleError, BundleResolutionError,  \
    WaitTimeoutError, InsecureFilePermissions, NOT_FOUND_ERROR
from subprocess import CalledProcessError


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


def handle_ambiguous_vm_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AmbiguousDockerVmError:
            log = get_logger_for_func(func)
            log.error('Docker native is installed and Docker machine environment variables are set.')
            log.error('It is uncertain which Docker VM should be used.')
            log.error('If Docker native should be used please unset the Docker machine environment variables:')
            log.error('  DOCKER_CERT_PATH')
            log.error('  DOCKER_HOST')
            log.error('  DOCKER_MACHINE_NAME')
            log.error('  DOCKER_TLS_VERIFY')
            log.error('If Docker machine should be used please uninstall Docker native.')

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_docker_machine_not_running_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DockerMachineNotRunningError:
            vm_name = docker_machine.vm_name()
            log = get_logger_for_func(func)
            log.error('Docker machine VM has not been started.')
            log.error('Use the following command to start the VM:')
            log.error('  docker-machine start {}'.format(vm_name))

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_docker_machine_cannot_connect_to_docker_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DockerMachineCannotConnectToDockerError:
            log = get_logger_for_func(func)
            log.info('It looks like the Docker machine environment variables are not set correctly.')
            log.info('Let me try to reset the Docker machine environment variables..')
            docker_machine_vm_name = docker_machine.vm_name()
            [docker_machine.set_env(env[0], env[1]) for env in docker_machine.envs(docker_machine_vm_name)]
            try:
                terminal.docker_info()
                log.warning('To set the environment variables for each terminal session '
                            'follow the instructions of the command:')
                log.warning('  docker-machine env {}'.format(docker_machine_vm_name))
                return func(*args, **kwargs)
            except (AttributeError, CalledProcessError):
                log.error('Docker still cannot connect to the Docker machine VM.')
                log.error('Please set the docker environment variables.')
                log.error('Afterwards verify that docker is up and running with: docker info')

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_vbox_manage_not_found_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NOT_FOUND_ERROR:
            log = get_logger_for_func(func)
            log.error('VBoxManage command not found')
            log.error('Make sure VirtualBox is installed and VBoxManage is in the path')
            exit(1)

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
