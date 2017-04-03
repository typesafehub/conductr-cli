from conductr_cli import sandbox_common
from conductr_cli.screen_utils import h1
import os
import signal
import logging
import time


def stop(args):
    """
    Stops the existing ConductR core and agent processes.
    This is done by interrogating the output of the ps, looking for java process which is running of the sandbox image.
    directory.

    :param args: args parsed from the input arguments
    """
    log = logging.getLogger(__name__)
    core_info, agent_info = sandbox_common.resolve_conductr_info(args.image_dir)

    pids_info = sandbox_common.find_pids(core_info['extraction_dir'], agent_info['extraction_dir'])
    if pids_info:
        log.info(h1('Stopping ConductR'))
        killed_pids_info, hung_pids_info = kill_processes(core_info, agent_info, pids_info)
        if hung_pids_info:
            for hung_pid_info in hung_pids_info:
                log.error('ConductR {} pid {} could not be stopped'.format(hung_pid_info['type'], hung_pid_info['id']))
            log.error('Please stop the processes manually')
            return False
        else:
            log.info('ConductR has been successfully stopped')
            return True
    else:
        return True


def kill_processes(core_info, agent_info, pids_info):
    """
    Kills the processes given the pids by sending SIGTERM.
    :param core_info: ConductR core information
    :param agent_info: ConductR agent information
    :param pids_info: List of pids info to be killed.
    :return: a tuple containing list of pids which has been killed successfully and a list of pids that were not killed
             using SIGTERM within 5 seconds.
    """
    log = logging.getLogger(__name__)

    def wait_for_processes(remaining_pids_info, killed_pids_info=[], attempt=1, max_attempts=10):
        time.sleep(1)
        new_remaining_pids_info = sandbox_common.find_pids(core_info['extraction_dir'], agent_info['extraction_dir'])
        new_killed_pids_info = [info for info in remaining_pids_info if info not in new_remaining_pids_info]
        for killed_pid_info in new_killed_pids_info:
            log.info('ConductR {} pid {} stopped'.format(killed_pid_info['type'], killed_pid_info['id']))
        killed_pids_info += new_killed_pids_info
        if not new_remaining_pids_info:
            return killed_pids_info, []
        elif attempt >= max_attempts:
            return killed_pids_info, new_remaining_pids_info
        else:
            return wait_for_processes(new_remaining_pids_info, killed_pids_info, attempt=attempt + 1)

    for pid_info in pids_info:
        os.kill(pid_info['id'], signal.SIGTERM)
    return wait_for_processes(pids_info)
