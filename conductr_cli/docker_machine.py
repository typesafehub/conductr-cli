import os
import logging

from conductr_cli import terminal
from subprocess import CalledProcessError
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


def vm_install_check(vm_name):
    try:
        output = terminal.docker_machine_status(vm_name)
        if output == 'Error':
            # Case: VM exists in docker-machine, but not in VirtualBox
            return False
        else:
            return True
    except CalledProcessError:
        # Case: VM does not exist in docker-machine
        return False


def running_check(vm_name):
    output = terminal.docker_machine_status(vm_name)
    return output == 'Running'


def ram_check(vm_name):
    existing_ram_size = terminal.vbox_manage_get_ram_size(vm_name)
    minimum_ram_size = int(DEFAULT_DOCKER_MACHINE_RAM_SIZE)
    has_sufficient_ram = existing_ram_size >= minimum_ram_size
    return existing_ram_size, has_sufficient_ram


def cpu_check(vm_name):
    existing_cpu_count = terminal.vbox_manage_get_cpu_count(vm_name)
    minimum_cpu_count = int(DEFAULT_DOCKER_MACHINE_CPU_COUNT)
    has_sufficient_cpu = existing_cpu_count >= minimum_cpu_count
    return existing_cpu_count, has_sufficient_cpu
