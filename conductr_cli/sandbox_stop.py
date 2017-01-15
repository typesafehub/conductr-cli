from conductr_cli import sandbox_proxy, sandbox_stop_docker, sandbox_stop_jvm
from subprocess import CalledProcessError


def stop(args):
    """`sandbox stop` command"""
    try:
        is_proxy_success = sandbox_proxy.stop_proxy()
    except (AttributeError, CalledProcessError):
        # Fail silently as these errors will be raised if Docker is not installed or Docker environment is not
        # configured properly.
        is_proxy_success = False

    is_docker_success = sandbox_stop_docker.stop(args)
    is_jvm_success = sandbox_stop_jvm.stop(args)
    return is_proxy_success and is_docker_success and is_jvm_success
