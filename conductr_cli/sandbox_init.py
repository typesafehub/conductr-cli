from conductr_cli import docker_machine, terminal
import logging
from subprocess import CalledProcessError


def init(args):
    """`sandbox init` command"""

    log = logging.getLogger(__name__)
    vm_name = docker_machine.vm_name()
    if is_docker_machine_installed():
        is_docker_vm_installed, output = docker_vm_install_check(vm_name)
        if not is_docker_vm_installed:
            log.info('Creating Docker VM {}'.format(vm_name))
            log.info('This will take a few minutes - please be patient...')
            terminal.docker_machine_create_vm(vm_name)

            log.info('Increasing RAM for Docker VM {}'.format(vm_name))
            log.info('We will need to stop the Docker VM {}, modify the RAM, and restart'.format(vm_name))

            log.info('Stopping Docker VM {}'.format(vm_name))
            terminal.docker_machine_stop_vm(vm_name)

            log.info('Increasing Docker VM {} RAM to {}MB'.format(vm_name,
                                                                  docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))
            terminal.vbox_manage_increase_ram(vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE)

            log.info('Starting Docker VM {}'.format(vm_name))
            terminal.docker_machine_start_vm(vm_name)
        else:
            log.info('Docker VM {} is already installed'.format(vm_name))

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
        output = terminal.docker_machine_env(vm_name)
        return True, output
    except CalledProcessError:
        return False, None
