from conductr_cli import host, terminal
import os


CONDUCTR_NAME_PREFIX = 'cond-'
CONDUCTR_PORTS = {9004,  # ConductR internal akka remoting
                  9005,  # ConductR controlServer
                  9006}  # ConductR bundleStreamServer
CONDUCTR_DEV_IMAGE = 'typesafe-docker-registry-for-subscribers-only.bintray.io/conductr/conductr'
LATEST_CONDUCTR_VERSION = '1.1.9'


host_ip = None


def resolve_host_ip():
    global host_ip
    if not host_ip:
        host_ip = host.resolve_default_ip()
    return host_ip


def resolve_running_docker_containers():
    """Resolve running docker containers.
       Return the running container names (e.g. cond-0) in ascending order"""
    container_ids = terminal.docker_ps(ps_filter='name={}'.format(CONDUCTR_NAME_PREFIX))
    container_names = [terminal.docker_inspect(container_id, '{{.Name}}')[1:] for container_id in container_ids]
    return sorted(container_names)


def bundle_http_port():
    """Returns ConductR default HAProxy Frontend port for HTTP based ACLs"""
    return int(os.getenv('BUNDLE_HTTP_PORT', 9000))
