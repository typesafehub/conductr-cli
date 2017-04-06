import os.path
import re
import logging
from conductr_cli import terminal
from conductr_cli.exceptions import DockerValidationError, NOT_FOUND_ERROR
from subprocess import CalledProcessError

DEFAULT_DOCKER_RAM_SIZE = 1.9
DEFAULT_DOCKER_CPU_COUNT = 2


class DockerVmType:
    DOCKER_ENGINE = 1
    DOCKER_MACHINE = 2
    NONE = 3


def vm_type():
    def docker_machine_envs_set():
        if os.getenv('DOCKER_MACHINE_NAME'):
            return True
        else:
            return False

    if docker_machine_envs_set():
        return DockerVmType.DOCKER_MACHINE
    elif os.path.exists('/var/run/docker.sock'):
        return DockerVmType.DOCKER_ENGINE
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


def is_docker_present():
    try:
        validate_docker_vm(vm_type())
        return True
    except DockerValidationError:
        return False


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
        except (AttributeError, CalledProcessError, NOT_FOUND_ERROR):
            raise DockerValidationError([
                'Docker is installed but not running.',
                'Please start Docker with one of the Docker flavors based on your OS:',
                '  Linux:   Docker service',
                '  MacOS:   Docker for Mac',
                'A successful Docker startup can be verified with: docker info'
            ])

    elif vm_type is DockerVmType.DOCKER_MACHINE:
        raise DockerValidationError([
            'Docker machine envs are set but Docker machine is not supported by the conductr-cli.',
            'We recommend to use one of following the Docker distributions depending on your OS:',
            '  Linux:                                         Docker Engine',
            '  MacOS:                                         Docker for Mac',
            'For more information checkout: https://www.docker.com/products/overview'
        ])

    elif vm_type is DockerVmType.NONE:
        raise DockerValidationError([
            'Docker is not installed.',
            'We recommend to use one of following the Docker distributions depending on your OS:',
            '  Linux:                                         Docker Engine',
            '  MacOS:                                         Docker for Mac',
            'For more information checkout: https://www.docker.com/products/overview'
        ])
