import os
from conductr_cli import terminal, validation, docker, docker_machine
from conductr_cli.docker import DockerVmType
from conductr_cli.exceptions import DockerMachineError
from subprocess import CalledProcessError


@validation.handle_docker_vm_error
def resolve_default_ip():
    def resolve():
        if docker.vm_type() == DockerVmType.DOCKER_ENGINE:
            return '127.0.0.1'
        else:
            return with_docker_machine()

    return os.getenv('CONDUCTR_IP', resolve())


def with_docker_machine():
    try:
        vm_name = docker_machine.vm_name()
        output = terminal.docker_machine_ip(vm_name)
        if output:
            return output
        else:
            raise DockerMachineError('docker-machine host is not running.')
    except CalledProcessError:
        raise DockerMachineError('docker-machine host is not running.')
