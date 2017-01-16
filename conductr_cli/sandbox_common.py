from conductr_cli import terminal
from conductr_cli.resolvers.bintray_resolver import BINTRAY_CONDUCTR_CORE_PACKAGE_NAME, \
    BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME
import os
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
