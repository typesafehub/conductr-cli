from conductr_cli import docker, docker_machine, terminal
import logging
import re
from subprocess import CalledProcessError


def init(args):
    """`sandbox init` command"""

    log = logging.getLogger(__name__)

    try:
        info = terminal.docker_info()
        existing_ram, has_sufficient_ram = docker_ram_check(info)
        existing_cpu, has_sufficient_cpu = docker_cpu_check(info)

        if not has_sufficient_ram or not has_sufficient_cpu:
            if not has_sufficient_ram:
                log.warning('Docker has insufficient RAM of {}MiB - please increase to a minimum of {}MiB'
                            .format(existing_ram, docker.DEFAULT_DOCKER_RAM_SIZE))

            if not has_sufficient_cpu:
                log.warning('Docker has an insufficient no. of CPUs {} - please increase to a minimum of {} CPUs'
                            .format(existing_cpu, docker.DEFAULT_DOCKER_CPU_COUNT))
        else:
            log.info('Docker already has sufficient RAM and CPUs')

    except (AttributeError, CalledProcessError):
        pass

    docker_machine_vm_name = docker_machine.vm_name()
    if is_docker_machine_installed():
        is_docker_machine_vm_installed = docker_machine_install_check(docker_machine_vm_name)
        if not is_docker_machine_vm_installed:
            log.info('Creating Docker machine VM {}'.format(docker_machine_vm_name))
            log.info('This will take a few minutes - please be patient...')
            terminal.docker_machine_create_vm(docker_machine_vm_name)
        else:
            log.info('Docker machine VM {} already installed'.format(docker_machine_vm_name))

        is_docker_machine_started = docker_machine_running_check(docker_machine_vm_name)
        if not is_docker_machine_started:
            log.info('Starting Docker machine VM {}'.format(docker_machine_vm_name))
            terminal.docker_machine_start_vm(docker_machine_vm_name)
        else:
            log.info('Docker machine VM {} already running'.format(docker_machine_vm_name))

        existing_ram, has_sufficient_ram = docker_machine_ram_check(docker_machine_vm_name)
        existing_cpu, has_sufficient_cpu = docker_machine_cpu_check(docker_machine_vm_name)

        if not has_sufficient_ram or not has_sufficient_cpu:
            if not has_sufficient_ram:
                log.warning('Docker machine VM {} has insufficient RAM of {}MiB - increasing to the minimum of {}MiB'
                            .format(docker_machine_vm_name,
                                    existing_ram,
                                    docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))

            if not has_sufficient_cpu:
                log.warning(
                    'Docker machine VM {} has an insufficient no. of CPUs {} - increasing to the minimum of {} CPU'
                    .format(docker_machine_vm_name, existing_cpu, docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT))

            log.info('Stopping Docker machine VM {}'.format(docker_machine_vm_name))
            terminal.docker_machine_stop_vm(docker_machine_vm_name)

            if not has_sufficient_ram:
                log.info(
                    'Increasing Docker machine VM {} RAM to {}MB'
                    .format(docker_machine_vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))
                terminal.vbox_manage_increase_ram(docker_machine_vm_name,
                                                  docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE)

            if not has_sufficient_cpu:
                log.info(
                    'Increasing Docker machine VM {} no. of CPUs to {}'
                    .format(docker_machine_vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT))
                terminal.vbox_manage_increase_cpu(docker_machine_vm_name,
                                                  docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT)

            log.info('Starting Docker machine VM {}'.format(docker_machine_vm_name))
            terminal.docker_machine_start_vm(docker_machine_vm_name)
        else:
            log.info('Docker machine VM {} already has sufficient RAM and CPUs'.format(docker_machine_vm_name))

        log.info('Sandbox initialization complete')


def docker_ram_check(info):
    m = re.search(b'.*\\nTotal Memory: (\d+(\.\d*)?).*', info)
    existing_ram_size = float(m.group(1))
    has_sufficient_ram = existing_ram_size >= docker.DEFAULT_DOCKER_RAM_SIZE
    return existing_ram_size, has_sufficient_ram


def docker_cpu_check(info):
    m = re.search(b'.*\\nCPUs: (\d+).*', info)
    existing_cpu_count = int(m.group(1))
    has_sufficient_cpu = existing_cpu_count >= docker.DEFAULT_DOCKER_CPU_COUNT
    return existing_cpu_count, has_sufficient_cpu


def is_docker_machine_installed():
    try:
        terminal.docker_machine_help()
        return True
    except CalledProcessError:
        return False


def docker_machine_install_check(vm_name):
    try:
        terminal.docker_machine_status(vm_name)
        return True
    except CalledProcessError:
        return False


def docker_machine_running_check(vm_name):
    output = terminal.docker_machine_status(vm_name)
    return output == 'Running'


def docker_machine_ram_check(vm_name):
    existing_ram_size = terminal.vbox_manage_get_ram_size(vm_name)
    minimum_ram_size = int(docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE)
    has_sufficient_ram = existing_ram_size >= minimum_ram_size
    return existing_ram_size, has_sufficient_ram


def docker_machine_cpu_check(vm_name):
    existing_cpu_count = terminal.vbox_manage_get_cpu_count(vm_name)
    minimum_cpu_count = int(docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT)
    has_sufficient_cpu = existing_cpu_count >= minimum_cpu_count
    return existing_cpu_count, has_sufficient_cpu
