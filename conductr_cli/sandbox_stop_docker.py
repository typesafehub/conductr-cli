from conductr_cli import sandbox_common, terminal
from conductr_cli.screen_utils import h1
from conductr_cli.exceptions import NOT_FOUND_ERROR
from subprocess import CalledProcessError
import logging


def stop(args):
    log = logging.getLogger(__name__)
    try:
        running_containers = sandbox_common.resolve_running_docker_containers()
    except (AttributeError, CalledProcessError, NOT_FOUND_ERROR):
        # return True because Docker is not installed and therefore no containers need to be stopped.
        return True

    if running_containers:
        log.info(h1('Stopping ConductR'))
        try:
            terminal.docker_rm(running_containers)
            log.info('ConductR has been successfully stopped')
            return True
        except (AttributeError, CalledProcessError, NOT_FOUND_ERROR):
            log.error('ConductR containers could not be stopped')
            log.error('Please stop the Docker containers manually')
            return False
    else:
        return True
