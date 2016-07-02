import os
from conductr_cli import terminal, validation, docker_machine
from conductr_cli.exceptions import DockerMachineError, Boot2DockerError
from subprocess import CalledProcessError


@validation.handle_docker_vm_error
def resolve_default_ip():
    def resolve():
        try:
            terminal.docker_info()
            return '127.0.0.1'
        except (CalledProcessError, FileNotFoundError):
            try:
                return with_docker_machine()
            except validation.NOT_FOUND_ERROR:
                try:
                    return with_boot2docker()
                except validation.NOT_FOUND_ERROR:
                    try:
                        return with_hostname()
                    except validation.NOT_FOUND_ERROR:
                        return '127.0.0.1'

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


def with_boot2docker():
    try:
        return terminal.boot2docker_ip()
    except CalledProcessError:
        raise Boot2DockerError('boot2docker host is not running.')


def with_hostname():
    return terminal.hostname()
