import os
from conductr_cli.constants import DEFAULT_PORT, DEFAULT_SANDBOX_ADDR_RANGE
import ipaddress
import socket
import platform
import sys


CONDUCTR_HOST = 'CONDUCTR_HOST'
CONDUCTR_IP = 'CONDUCTR_IP'
CONDUCTR_LISTEN_CHECK_TIMEOUT = 0.1  # Socket timeout (in seconds) for checking if ConductR is listening on an address.
DOCKER_IP = '127.0.0.1'


def resolve_default_host():
    return resolve_default_ip()


def resolve_default_ip():
    def result_from_default_addr_range():
        addr_range = ipaddress.ip_network(DEFAULT_SANDBOX_ADDR_RANGE, strict=True)
        addr = list(addr_range.hosts())[0]
        return addr.exploded if is_listening(addr, int(DEFAULT_PORT)) else None

    from_addr_range = result_from_default_addr_range()
    return from_addr_range if from_addr_range else DOCKER_IP


def resolve_host_from_env():
    return os.getenv(CONDUCTR_HOST, os.getenv(CONDUCTR_IP, None))


def hostname():
    return socket.gethostname()


def loopback_device_name():
    return 'lo' if is_linux() else 'lo0'


def is_linux():
    return platform.system().lower() == 'linux'


def is_macos():
    return platform.system().lower() == 'darwin'


def is_64bit():
    return sys.maxsize > 2**32


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


def addr_alias_commands(addrs, ip_version):
    if_name = loopback_device_name()

    subnet_mask = get_subnet_mask(ip_version)

    commands = []
    if is_linux():
        commands = [['sudo', 'ifconfig', '{}:{}'.format(if_name, int(addr.exploded[-1:]) - 1),
                     addr.exploded, 'netmask', subnet_mask, 'up'] for addr in addrs]
    elif is_macos():
        commands = [['sudo', 'ifconfig', if_name, 'alias', addr.exploded, subnet_mask] for addr in addrs]

    return commands


def get_subnet_mask(ip_version):
    # Note that the CIDR notation (e.g. /24) is for identifying the subnet to pick an address from.
    # For actually setting up the alias, we want to mask out the entire network so the alias only
    # responds to traffic for its own IP.
    masks = {
        4: "255.255.255.255",
        6: "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
    }

    return masks[ip_version]
