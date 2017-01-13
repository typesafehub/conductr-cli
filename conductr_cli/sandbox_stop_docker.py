from conductr_cli import sandbox_common, terminal
from conductr_cli.screen_utils import headline
from subprocess import CalledProcessError
import logging


def stop(args):
    log = logging.getLogger(__name__)
    running_containers = sandbox_common.resolve_running_docker_containers()
    if running_containers:
        log.info(headline('Stopping ConductR'))
        try:
            terminal.docker_rm(running_containers)
            log.info('ConductR has been successfully stopped')
            return True
        except (AttributeError, CalledProcessError):
            log.error('ConductR containers could not be stopped pid 58002 could not be stopped')
            log.error('Please stop the Docker containers manually')
            return False
    else:
        return True
