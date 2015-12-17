import os

DEFAULT_DOCKER_MACHINE_NAME = 'default'


def vm_name():
    return os.getenv('DOCKER_MACHINE_NAME', DEFAULT_DOCKER_MACHINE_NAME)
