import os
from conductr_cli import platform, terminal


DEFAULT_DOCKER_VM_NAME = 'default'
DEFAULT_DOCKER_VM_RAM_SIZE = '3072'
DEFAULT_DOCKER_VM_CPU_COUNT = '4'


class DockerVmType:
    DOCKER_ENGINE = 1
    DOCKER_MACHINE = 2


def vm_type():
    is_linux = platform.is_linux()
    if is_linux:
        return DockerVmType.DOCKER_ENGINE
    else:
        version = terminal.docker_version()
        if version >= 1.12 and not os.getenv('DOCKER_MACHINE_NAME'):
            return DockerVmType.DOCKER_ENGINE
        else:
            return DockerVmType.DOCKER_MACHINE


def vm_name():
    return os.getenv('DOCKER_MACHINE_NAME', DEFAULT_DOCKER_VM_NAME)
