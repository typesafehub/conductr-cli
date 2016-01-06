from conductr_cli import docker_machine, terminal
import logging
from subprocess import CalledProcessError


def init(args):
    """`sandbox init` command"""

    log = logging.getLogger(__name__)
    vm_name = docker_machine.vm_name()
    if is_docker_machine_installed():
        is_docker_vm_installed = docker_vm_install_check(vm_name)
        if not is_docker_vm_installed:
            log.info('Creating Docker VM {}'.format(vm_name))
            log.info('This will take a few minutes - please be patient...')
            terminal.docker_machine_create_vm(vm_name)
        else:
            log.info('Docker VM {} already installed'.format(vm_name))

        is_docker_vm_started = docker_vm_running_check(vm_name)
        if not is_docker_vm_started:
            log.info('Starting Docker VM {}'.format(vm_name))
            terminal.docker_machine_start_vm(vm_name)
        else:
            log.info('Docker VM {} already running'.format(vm_name))

        existing_ram, has_sufficient_ram = docker_vm_ram_check(vm_name)
        existing_cpu, has_sufficient_cpu = docker_vm_cpu_check(vm_name)

        if not has_sufficient_ram or not has_sufficient_cpu:
            if not has_sufficient_ram:
                log.warning('Docker VM {} has insufficient RAM of {}MB - increasing to the minimum of {}MB'
                            .format(vm_name, existing_ram, docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))

            if not has_sufficient_cpu:
                log.warning('Docker VM {} has insufficient no of CPU {} - increasing to the minimum of {} CPU'
                            .format(vm_name, existing_cpu, docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT))

            log.info('Stopping Docker VM {}'.format(vm_name))
            terminal.docker_machine_stop_vm(vm_name)

            if not has_sufficient_ram:
                log.info('Increasing Docker VM {} RAM to {}MB'.format(vm_name,
                                                                      docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))
                terminal.vbox_manage_increase_ram(vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE)

            if not has_sufficient_cpu:
                log.info('Increasing Docker VM {} no of CPU to {}'
                         .format(vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT))
                terminal.vbox_manage_increase_cpu(vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT)

            log.info('Starting Docker VM {}'.format(vm_name))
            terminal.docker_machine_start_vm(vm_name)
        else:
            log.info('Docker VM {} already has sufficient RAM and CPU'.format(vm_name))

        log.info('Sandbox initialization complete')
    else:
        log.warning('Unable to initialize sandbox - docker-machine not installed')


def is_docker_machine_installed():
    try:
        terminal.docker_machine_help()
        return True
    except CalledProcessError:
        return False


def docker_vm_install_check(vm_name):
    try:
        terminal.docker_machine_status(vm_name)
        return True
    except CalledProcessError:
        return False


def docker_vm_running_check(vm_name):
    output = terminal.docker_machine_status(vm_name)
    return output == 'Running'


def docker_vm_ram_check(vm_name):
    existing_ram_size = terminal.vbox_manage_get_ram_size(vm_name)
    minimum_ram_size = int(docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE)
    has_sufficient_ram = existing_ram_size >= minimum_ram_size
    return existing_ram_size, has_sufficient_ram


def docker_vm_cpu_check(vm_name):
    existing_cpu_count = terminal.vbox_manage_get_cpu_count(vm_name)
    minimum_cpu_count = int(docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT)
    has_sufficient_cpu = existing_cpu_count >= minimum_cpu_count
    return existing_cpu_count, has_sufficient_cpu
