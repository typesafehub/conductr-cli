from conductr_cli import terminal
from conductr_cli.resolvers.bintray_resolver import BINTRAY_CONDUCTR_CORE_PACKAGE_NAME, \
    BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME
import os
import re
import subprocess
from subprocess import CalledProcessError


CONDUCTR_NAME_PREFIX = 'cond-'
CONDUCTR_PORTS = {9004,  # ConductR internal akka remoting
                  9005,  # ConductR controlServer
                  9006}  # ConductR bundleStreamServer
CONDUCTR_DEV_IMAGE = 'typesafe-docker-registry-for-subscribers-only.bintray.io/conductr/conductr'


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


def find_pids(core_run_dir, agent_run_dir):
    """
    Finds the PIDs of ConductR core and agent from the output of the ps process, looking for java process
    which is running of the sandbox image.
    :param core_run_dir: directory of where ConductR core is running from.
    :param agent_run_dir: directory of where ConductR agent is running from.
    :return: the list of the ConductR core and agent pids.
    """
    pids_info = []
    ps_output = subprocess.getoutput('ps ax')
    for line in ps_output.split('\n'):
        def extract_param(regex, default):
            try:
                return re.search(regex, line).group(1)
            except AttributeError:
                return default

        pid = line.split()[0]
        if core_run_dir in line:
            pids_info.append({
                'type': 'core',
                'id': int(pid),
                'ip': extract_param('-Dconductr.ip=(\S+)', '')
            })
        if agent_run_dir in line:
            pids_info.append({
                'type': 'agent',
                'id': int(pid),
                'ip': extract_param('-Dconductr.agent.ip=(\S+)', '')
            })
    return pids_info


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


def major_version(version):
    return int(version[0])


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
