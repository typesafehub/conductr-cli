import os.path
import re
import logging
from conductr_cli.exceptions import AmbiguousDockerVmError
from conductr_cli import validation, docker_machine, terminal
from subprocess import CalledProcessError

DEFAULT_DOCKER_RAM_SIZE = 3.8
DEFAULT_DOCKER_CPU_COUNT = 4


class DockerVmType:
    DOCKER_ENGINE = 1
    DOCKER_MACHINE = 2
    NONE = 3


@validation.handle_ambiguous_vm_error
def vm_type():
    # TODO: Add Docker native check for Windows 10 Professional and Enterprise Edition
    docker_machine_name_env = os.getenv('DOCKER_MACHINE_NAME')

    def docker_machine_envs_set():
        if docker_machine_name_env:
            return True
        else:
            return False

    if os.path.exists('/var/run/docker.sock'):
        if docker_machine_envs_set():
            raise AmbiguousDockerVmError(
                'Native docker is installed and docker-machine environment variables are set.')
        else:
            return DockerVmType.DOCKER_ENGINE
    elif docker_machine_envs_set():
        return DockerVmType.DOCKER_MACHINE
    else:
        return DockerVmType.NONE


def ram_check(info):
    m = re.search(b'.*\\nTotal Memory: (\d+(\.\d*)?).*', info)
    existing_ram_size = float(m.group(1))
    has_sufficient_ram = existing_ram_size >= DEFAULT_DOCKER_RAM_SIZE
    return existing_ram_size, has_sufficient_ram


def cpu_check(info):
    m = re.search(b'.*\\nCPUs: (\d+).*', info)
    existing_cpu_count = int(m.group(1))
    has_sufficient_cpu = existing_cpu_count >= DEFAULT_DOCKER_CPU_COUNT
    return existing_cpu_count, has_sufficient_cpu


@validation.handle_vbox_manage_not_found_error
def validate_docker_vm(vm_type):
    log = logging.getLogger(__name__)
    if vm_type is DockerVmType.DOCKER_ENGINE:
        try:
            info = terminal.docker_info()
            existing_ram, has_sufficient_ram = ram_check(info)
            existing_cpu, has_sufficient_cpu = cpu_check(info)

            if not has_sufficient_ram or not has_sufficient_cpu:
                if not has_sufficient_ram:
                    log.warning('Docker has insufficient RAM of {} GiB - please increase to a minimum of {} GiB'
                                .format(existing_ram, DEFAULT_DOCKER_RAM_SIZE))

                if not has_sufficient_cpu:
                    log.warning('Docker has an insufficient no. of CPUs {} - please increase to a minimum of {} CPUs'
                                .format(existing_cpu, DEFAULT_DOCKER_CPU_COUNT))
        except (AttributeError, CalledProcessError):
            log.error('Docker native is installed but not running.')
            log.error('Please start Docker with one of the Docker flavors based on your OS:')
            log.error('  Linux:   Docker service')
            log.error('  MacOS:   Docker for Mac')
            log.error('  Windows: Docker for Windows')
            log.error('A successful Docker startup can be verified with: docker info')
            exit(1)

    elif vm_type is DockerVmType.DOCKER_MACHINE:
        docker_machine_vm_name = docker_machine.vm_name()

        is_docker_machine_vm_installed = docker_machine.vm_install_check(docker_machine_vm_name)
        if not is_docker_machine_vm_installed:
            log.info('Creating Docker machine VM {}'.format(docker_machine_vm_name))
            log.info('This will take a few minutes - please be patient..')
            terminal.docker_machine_create_vm(docker_machine_vm_name)

        is_docker_machine_started = docker_machine.running_check(docker_machine_vm_name)
        if not is_docker_machine_started:
            log.info('Starting Docker machine VM {}'.format(docker_machine_vm_name))
            terminal.docker_machine_start_vm(docker_machine_vm_name)

        existing_ram, has_sufficient_ram = docker_machine.ram_check(docker_machine_vm_name)
        existing_cpu, has_sufficient_cpu = docker_machine.cpu_check(docker_machine_vm_name)

        if not has_sufficient_ram or not has_sufficient_cpu:
            if not has_sufficient_ram:
                log.warning('Docker machine VM {} has insufficient RAM of {} MB - '
                            'increasing to the minimum of {} MB'
                            .format(docker_machine_vm_name,
                                    existing_ram,
                                    docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))

            if not has_sufficient_cpu:
                log.warning('Docker machine VM {} has an insufficient no. of CPUs {} - '
                            'increasing to the minimum of {} CPU'
                            .format(docker_machine_vm_name, existing_cpu,
                                    docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT))

            log.info('Stopping Docker machine VM {}'.format(docker_machine_vm_name))
            terminal.docker_machine_stop_vm(docker_machine_vm_name)

            if not has_sufficient_ram:
                log.info('Increasing Docker machine VM {} RAM to {} MB'
                         .format(docker_machine_vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE))
                terminal.vbox_manage_increase_ram(docker_machine_vm_name,
                                                  docker_machine.DEFAULT_DOCKER_MACHINE_RAM_SIZE)

            if not has_sufficient_cpu:
                log.info('Increasing Docker machine VM {} no. of CPUs to {}'
                         .format(docker_machine_vm_name, docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT))
                terminal.vbox_manage_increase_cpu(docker_machine_vm_name,
                                                  docker_machine.DEFAULT_DOCKER_MACHINE_CPU_COUNT)

            log.info('Starting Docker machine VM {}'.format(docker_machine_vm_name))
            terminal.docker_machine_start_vm(docker_machine_vm_name)

            try:
                terminal.docker_info()
            except (AttributeError, CalledProcessError):
                log.info('It looks like the Docker machine environment variables are not set correctly.')
                log.info('Let me try to reset the Docker machine environment variables..')
                [docker_machine.set_env(env[0], env[1]) for env in docker_machine.envs(docker_machine_vm_name)]
                try:
                    terminal.docker_info()
                    log.warning('To set the environment variables for each terminal session '
                                'follow the instructions of the command:')
                    log.warning('  docker-machine env {}'.format(docker_machine_vm_name))
                except (AttributeError, CalledProcessError):
                    log.error('Docker still cannot connect to the Docker machine VM.')
                    log.error('Please set the docker environment variables.')
                    log.error('Afterwards verify that docker is up and running with: docker info')
                    exit(1)

    elif vm_type is DockerVmType.NONE:
        log.error('Neither Docker native is installed nor the Docker machine environment variables are set.')
        log.error('We recommend to use one of following the Docker distributions depending on your OS:')
        log.error('  Linux:                                         Docker Engine')
        log.error('  MacOS:                                         Docker for Mac')
        log.error('  Windows 10+ Professional or Enterprise 64-bit: Docker for Windows')
        log.error('  Other Windows:                                 Docker machine via Docker Toolbox')
        log.error('For more information checkout: https://www.docker.com/products/overview')
        exit(1)
