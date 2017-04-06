from conductr_cli import conduct_main, docker, terminal
from conductr_cli.constants import DEFAULT_SANDBOX_PROXY_DIR, DEFAULT_SANDBOX_PROXY_CONTAINER_NAME
from conductr_cli.exceptions import NOT_FOUND_ERROR
from conductr_cli.screen_utils import h1
from subprocess import CalledProcessError
import logging
import os


HAPROXY_VERSION = '1.5'
HAPROXY_DOCKER_IMAGE = 'haproxy:{}'.format(HAPROXY_VERSION)

HAPROXY_CFG_DIR = '{}/haproxy'.format(DEFAULT_SANDBOX_PROXY_DIR)
HAPROXY_CFG_PATH = '{}/haproxy.cfg'.format(HAPROXY_CFG_DIR)
DEFAULT_PROXY_PORTS = [80, 443, 8999]  # These are the ports which will be opened by default to the proxy.

# This is the default config which will be supplied so HAProxy instance within Docker can be started.
DEFAULT_HAPROXY_CFG_ENTRIES = 'defaults\n' \
                              '  log global\n' \
                              '  mode    http\n' \
                              '  option  httplog\n' \
                              '  option  dontlognull\n' \
                              '  timeout connect 5000\n' \
                              '  timeout client  50000\n' \
                              '  timeout server  50000\n' \
                              '\n' \
                              'frontend conductr-haproxy-test\n' \
                              '  bind :65535\n' \
                              '  mode http\n' \
                              '  monitor-uri /test\n' \
                              ''


def start_proxy(proxy_bind_addr, bundle_http_port, proxy_ports, all_feature_ports):
    if docker.is_docker_present():
        setup_haproxy_dirs()
        stop_proxy()
        start_docker_instance(proxy_bind_addr, bundle_http_port, proxy_ports, all_feature_ports)
        start_conductr_haproxy()
        return True
    else:
        return False


def stop_proxy():
    log = logging.getLogger(__name__)

    if docker.is_docker_present():
        try:
            running_container = get_running_haproxy()
            if running_container:
                log.info(h1('Stopping HAProxy'))
                terminal.docker_rm([DEFAULT_SANDBOX_PROXY_CONTAINER_NAME])
                log.info('HAProxy has been successfully stopped')

            return True
        except (AttributeError, CalledProcessError, NOT_FOUND_ERROR):
            return False
    else:
        # Docker is not present, so the proxy feature won't be running in the first place.
        return True


def setup_haproxy_dirs():
    os.makedirs(HAPROXY_CFG_DIR, exist_ok=True, mode=0o700)

    # Correct haproxy.cfg file must exists in order for Docker image to be working
    if not os.path.exists(HAPROXY_CFG_PATH):
        with open(HAPROXY_CFG_PATH, 'w') as haproxy_cfg:
            haproxy_cfg.write(DEFAULT_HAPROXY_CFG_ENTRIES)


def get_running_haproxy():
    return terminal.docker_ps(ps_filter='name={}'.format(DEFAULT_SANDBOX_PROXY_CONTAINER_NAME))


def start_docker_instance(proxy_bind_addr, bundle_http_port, proxy_ports, all_feature_ports):
    log = logging.getLogger(__name__)
    log.info(h1('Starting HAProxy'))

    docker_image = terminal.docker_images(HAPROXY_DOCKER_IMAGE)
    if not docker_image:
        log.info('Pulling docker image {}'.format(HAPROXY_DOCKER_IMAGE))
        terminal.docker_pull(HAPROXY_DOCKER_IMAGE)

    all_proxy_ports = [bundle_http_port]
    all_proxy_ports.extend(DEFAULT_PROXY_PORTS)
    all_proxy_ports.extend(all_feature_ports)
    all_proxy_ports.extend(proxy_ports)
    all_proxy_ports = sorted(set(all_proxy_ports))

    port_args = []
    for port in all_proxy_ports:
        port_args.append('-p')
        port_args.append('{}:{}:{}'.format(proxy_bind_addr.exploded, port, port))

    docker_args = ['-d', '--name', DEFAULT_SANDBOX_PROXY_CONTAINER_NAME] + port_args + \
                  ['-v', '{}:/usr/local/etc/haproxy:ro'.format(HAPROXY_CFG_DIR)]

    log.info('Exposing the following ports {}'.format(all_proxy_ports))
    terminal.docker_run(docker_args, HAPROXY_DOCKER_IMAGE, positional_args=[])


def start_conductr_haproxy():
    log = logging.getLogger(__name__)
    bundle_name = 'conductr-haproxy'
    configuration_name = 'conductr-haproxy-dev-mode'
    log.info('Deploying bundle {} with configuration {}'.format(bundle_name, configuration_name))
    conduct_main.run(['load', bundle_name, configuration_name, '--disable-instructions'], configure_logging=False)
    conduct_main.run(['run', bundle_name, '--disable-instructions'], configure_logging=False)
