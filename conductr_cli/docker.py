import os.path
from conductr_cli.exceptions import AmbiguousDockerVmError
from conductr_cli import validation

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
    docker_host_env = os.getenv('DOCKER_HOST')
    docker_tls_verify_env = os.getenv('DOCKER_TLS_VERIFY')
    docker_cert_path_env = os.getenv('DOCKER_CERT_PATH')

    def docker_machine_envs_set():
        if docker_machine_name_env or docker_host_env or docker_tls_verify_env or docker_cert_path_env:
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
