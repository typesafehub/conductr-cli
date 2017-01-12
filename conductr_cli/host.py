import os
from conductr_cli import terminal, validation, docker_machine, docker
from conductr_cli.constants import DEFAULT_PORT, DEFAULT_SANDBOX_ADDR_RANGE
from conductr_cli.exceptions import DockerMachineNotRunningError
from subprocess import CalledProcessError
from conductr_cli.docker import DockerVmType
import ipaddress
import socket
import platform


CONDUCTR_HOST = 'CONDUCTR_HOST'
CONDUCTR_IP = 'CONDUCTR_IP'
CONDUCTR_LISTEN_CHECK_TIMEOUT = 0.1  # Socket timeout (in seconds) for checking if ConductR is listening on an address.


def resolve_default_host():
    return os.getenv(CONDUCTR_HOST, resolve_default_ip())


def resolve_default_ip():
    def result_from_default_addr_range():
        addr_range = ipaddress.ip_network(DEFAULT_SANDBOX_ADDR_RANGE, strict=True)
        addr = list(addr_range.hosts())[0]
        return addr.exploded if is_listening(addr, int(DEFAULT_PORT)) else None

    def resolve_from_docker():
        vm_type = docker.vm_type()
        return resolve_ip_by_vm_type(vm_type)

    def resolve():
        from_addr_range = result_from_default_addr_range()
        return from_addr_range if from_addr_range else resolve_from_docker()

    return os.getenv(CONDUCTR_IP, resolve())


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


def loopback_device_name():
    return 'lo' if is_linux() else 'lo0'


def is_linux():
    return platform.system().lower() == 'linux'


def is_macos():
    return platform.system().lower() == 'darwin'


def can_bind(ip_addr, port):
    socket_af = socket.AF_INET if ip_addr.version == 4 else socket.AF_INET6
    s = socket.socket(socket_af, socket.SOCK_STREAM)

    result = False
    try:
        s.bind((ip_addr.exploded, port))
        result = True
    except OSError:
        pass
    finally:
        s.close()

    return result


def is_listening(ip_addr, port):
    socket_af = socket.AF_INET if ip_addr.version == 4 else socket.AF_INET6
    s = socket.socket(socket_af, socket.SOCK_STREAM)

    result = False
    try:
        s.settimeout(CONDUCTR_LISTEN_CHECK_TIMEOUT)
        s.connect((ip_addr.exploded, port))
        result = True
    except OSError:
        pass
    finally:
        s.close()

    return result


def addr_alias_setup_instructions(addrs, subnet_mask):
    def info_text(commands):
        if len(commands) > 1:
            return 'Run the following commands to create the address aliases on your machine:'
        else:
            return 'Run the following command to create an address alias on your machine:'

    if_name = loopback_device_name()

    if is_linux():
        commands = ['sudo ifconfig {}:{} {} netmask {} up'.format(if_name, idx, addr.exploded, subnet_mask)
                    for idx, addr in enumerate(addrs)]

        return '{}\n' \
               '\n' \
               '{}\n' \
               ''.format(info_text(commands), '\n'.join(commands))

    elif is_macos():
        commands = ['sudo ifconfig {} alias {} {}'.format(if_name, addr.exploded, subnet_mask) for addr in addrs]
        return '{}\n' \
               '\n' \
               '{}\n' \
               ''.format(info_text(commands), '\n'.join(commands))
    else:
        return 'Setup alias for {} addresses with {} subnet mask'.format(display_addrs(addrs), subnet_mask)


def display_addrs(addrs, separator=', '):
    return separator.join(['{}'.format(addr) for addr in addrs])
