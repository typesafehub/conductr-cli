import os
import logging

from conductr_cli import terminal
from conductr_cli.exceptions import NOT_FOUND_ERROR

DEFAULT_DOCKER_MACHINE_NAME = 'default'
DEFAULT_DOCKER_MACHINE_RAM_SIZE = '4096'
DEFAULT_DOCKER_MACHINE_CPU_COUNT = '4'


def vm_name():
    return os.getenv('DOCKER_MACHINE_NAME', DEFAULT_DOCKER_MACHINE_NAME)


def envs(docker_machine_vm_name):
    def resolve_env(line):
        key = line.partition(' ')[-1].partition('=')[0]
        value = line.partition(' ')[-1].partition('=')[2].strip('"')
        return key, value

    try:
        env_lines = terminal.docker_machine_env(docker_machine_vm_name)
        log = logging.getLogger(__name__)
        log.info('Retrieved docker environment variables with: docker-machine env {}'.format(docker_machine_vm_name))
    except NOT_FOUND_ERROR:
        return []
    return [resolve_env(line) for line in env_lines if line.startswith('export') or line.startswith('SET')]


def set_env(key, value):
    log = logging.getLogger(__name__)
    log.info('Set environment variable: {}="{}"'.format(key, value))
    os.environ[key] = value
