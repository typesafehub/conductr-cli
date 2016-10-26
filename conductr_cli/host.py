import os
from conductr_cli import terminal, validation, docker_machine, docker
from conductr_cli.exceptions import DockerMachineNotRunningError
from subprocess import CalledProcessError
from conductr_cli.docker import DockerVmType


def resolve_default_ip():
    def resolve():
        vm_type = docker.vm_type()
        return resolve_ip_by_vm_type(vm_type)

    return os.getenv('CONDUCTR_IP', resolve())


def resolve_ip_by_vm_type(vm_type):
    if vm_type is DockerVmType.NONE or vm_type is DockerVmType.DOCKER_ENGINE:
        return '127.0.0.1'
    elif vm_type is DockerVmType.DOCKER_MACHINE:
        return with_docker_machine()


@validation.handle_docker_machine_not_running_error
def with_docker_machine():
    try:
        vm_name = docker_machine.vm_name()
        output = terminal.docker_machine_ip(vm_name)
        if output:
            return output
        else:
            raise DockerMachineNotRunningError('docker-machine host is not running.')
    except CalledProcessError:
        raise DockerMachineNotRunningError('docker-machine host is not running.')
