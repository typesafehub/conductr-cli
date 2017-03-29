from conductr_cli import conduct_url, conduct_request, terminal
from conductr_cli.resolvers.bintray_resolver import BINTRAY_CONDUCTR_CORE_PACKAGE_NAME, \
    BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME
from conductr_cli.constants import DEFAULT_CLI_TMP_DIR
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from conductr_cli.exceptions import ConductrStartupError
from requests.exceptions import ConnectionError
from subprocess import CalledProcessError
import logging
import os
import psutil
import re
import time


CONDUCTR_NAME_PREFIX = 'cond-'
CONDUCTR_PORTS = {9004,  # ConductR internal akka remoting
                  9005,  # ConductR controlServer
                  9006}  # ConductR bundleStreamServer
CONDUCTR_DEV_IMAGE = 'typesafe-docker-registry-for-subscribers-only.bintray.io/conductr/conductr'

# Will retry 30 times, every two seconds
DEFAULT_WAIT_RETRIES = 30
DEFAULT_WAIT_RETRY_INTERVAL = 2.0

LATEST_SANDBOX_RUN_ARGS_FILE = '{}/latest_sandbox_run_args'.format(DEFAULT_CLI_TMP_DIR)


def resolve_conductr_info(image_dir):
    core_info = {
        'type': 'core',
        'extraction_dir': '{}/core'.format(image_dir),
        'bintray_package_name': BINTRAY_CONDUCTR_CORE_PACKAGE_NAME
    }
    agent_info = {
        'type': 'agent',
        'extraction_dir': '{}/agent'.format(image_dir),
        'bintray_package_name': BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME
    }
    return core_info, agent_info


def raw_process_info():
    processes = []

    for proc in psutil.process_iter():
        try:
            processes.append(proc.as_dict(attrs=['pid', 'name', 'cmdline']))
        except psutil.NoSuchProcess:
            pass

    return processes


def calculate_pids(core_run_dir, agent_run_dir, ps):
    pids_info = []

    for process in ps:
        def extract_param(regex, default):
            for e in process['cmdline']:
                try:
                    return re.search(regex, e).group(1)
                except AttributeError:
                    pass

            return default

        if process['name'] and process['name'] == 'java' and \
                process['cmdline'] and any('-Dconductr.ip=' in e for e in process['cmdline']) and \
                any(core_run_dir in e for e in process['cmdline']):
            pids_info.append({
                'type': 'core',
                'id': int(process['pid']),
                'ip': extract_param('-Dconductr.ip=(\S+)', '')
            })
        elif process['name'] and process['name'] == 'java' and \
                process['cmdline'] and \
                any('-Dconductr.agent.ip=' in e for e in process['cmdline']) and \
                any(agent_run_dir in e for e in process['cmdline']):
            pids_info.append({
                'type': 'agent',
                'id': int(process['pid']),
                'ip': extract_param('-Dconductr.agent.ip=(\S+)', '')
            })

    return pids_info


def find_pids(core_run_dir, agent_run_dir):
    """
    Finds the PIDs of ConductR core and agent from the output of the ps process, looking for java process
    which is running of the sandbox image.
    :param core_run_dir: directory of where ConductR core is running from.
    :param agent_run_dir: directory of where ConductR agent is running from.
    :return: the list of the ConductR core and agent pids.
    """

    return calculate_pids(core_run_dir, agent_run_dir, raw_process_info())


def resolve_running_docker_containers():
    """Resolve running docker containers.
       Return the running container names (e.g. cond-0) in ascending order"""
    try:
        container_ids = terminal.docker_ps(ps_filter='name={}'.format(CONDUCTR_NAME_PREFIX))
        container_names = [terminal.docker_inspect(container_id, '{{.Name}}')[1:] for container_id in container_ids]
        return sorted(container_names)
    except (AttributeError, CalledProcessError):
        return []


def bundle_http_port():
    """Returns ConductR default HAProxy Frontend port for HTTP based ACLs"""
    return int(os.getenv('BUNDLE_HTTP_PORT', 9000))


def resolve_conductr_roles_by_instance(user_conductr_roles, feature_conductr_roles, instance):
    if not user_conductr_roles:
        # No ConductR roles have been specified => Return an empty list
        return []
    else:
        if instance + 1 <= len(user_conductr_roles):
            # Roles have been specified for the current ConductR instance => Get and use these roles.
            container_conductr_roles = user_conductr_roles[instance]
        else:
            # The current ConductR instance is greater than the length of conductr_roles.
            # In this case the roles of conductr_roles are subsequently applied to the remaining instances.
            remainder = (instance + 1) % len(user_conductr_roles)
            remaining_instance = len(user_conductr_roles) if remainder == 0 else remainder
            container_conductr_roles = user_conductr_roles[remaining_instance - 1]

        # Feature roles are only added to the seed node.
        if instance == 0:
            container_conductr_roles = container_conductr_roles + feature_conductr_roles

        return container_conductr_roles


def flatten(list):
    return [item for sublist in list for item in sublist]


def wait_for_start(run_result):
    retries = int(os.getenv('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES))
    interval = float(os.getenv('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL))
    is_conductr_started = wait_for_conductr(run_result, 0, retries, interval)
    if not is_conductr_started:
        raise ConductrStartupError(wait_timeout=retries * interval, error_log_file=run_result.conductr_log_file)
    return True


def wait_for_conductr(run_result, current_retry, max_retries, interval):
    log = logging.getLogger(__name__)
    last_message = 'Waiting for ConductR to start'
    log.progress(last_message, flush=False)
    for attempt in range(0, max_retries):
        time.sleep(interval)

        last_message = '{}.'.format(last_message)
        log.progress(last_message, flush=False)

        url = conduct_url.url('members', run_result)
        try:
            conduct_request.get(dcos_mode=False, host=run_result.host, url=url, timeout=DEFAULT_HTTP_TIMEOUT)
            break
        except ConnectionError:
            current_retry += 1

    # Reprint previous message with flush to go to next line
    log.progress(last_message, flush=True)
    return True if current_retry < max_retries else False
