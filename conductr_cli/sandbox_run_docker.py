from conductr_cli import host, sandbox_common, sandbox_stop, terminal
from conductr_cli.constants import DEFAULT_SCHEME, DEFAULT_PORT, DEFAULT_BASE_PATH, DEFAULT_API_VERSION
from conductr_cli.exceptions import InstanceCountError
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE, CONDUCTR_NAME_PREFIX, CONDUCTR_PORTS, flatten
from conductr_cli.screen_utils import h1

import logging
import os


class SandboxRunResult:
    def __init__(self, container_names, conductr_host, wait_for_conductr):
        self.container_names = container_names
        self.host = conductr_host
        self.wait_for_conductr = wait_for_conductr

    scheme = DEFAULT_SCHEME
    port = DEFAULT_PORT
    base_path = DEFAULT_BASE_PATH
    api_version = DEFAULT_API_VERSION

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False


def run(args, features):
    nr_of_containers = instance_count(args.image_version, args.nr_of_instances)
    pull_image(args)
    container_names = scale_cluster(args, nr_of_containers, features)
    return SandboxRunResult(container_names, host.DOCKER_IP, wait_for_conductr=True)


def log_run_attempt(args, run_result, feature_results, feature_provided):
    log = logging.getLogger(__name__)
    container_names = run_result.container_names
    log.info(h1('Summary'))
    log.info('ConductR has been started')
    plural_string = 's' if len(container_names) > 1 else ''
    log.info('Check resource consumption of Docker container{} that run the ConductR node{} with:'
             .format(plural_string, plural_string))
    log.info('  docker stats {}'.format(' '.join(container_names)))
    log.info('Check current bundle status with:')
    log.info('  conduct info')


def instance_count(image_version, nr_of_containers):
    try:
        return int(nr_of_containers)
    except ValueError:
        raise InstanceCountError(image_version,
                                 nr_of_containers,
                                 'Number of containers must be an integer')


def pull_image(args):
    if args.image == CONDUCTR_DEV_IMAGE and not terminal.docker_images(CONDUCTR_DEV_IMAGE):
        log = logging.getLogger(__name__)
        log.info('Pulling down the ConductR development image..')
        terminal.docker_pull('{image_name}:{image_version}'
                             .format(image_name=CONDUCTR_DEV_IMAGE, image_version=args.image_version))


def scale_cluster(args, nr_of_containers, features):
    sandbox_stop.stop(args)
    return start_nodes(args, nr_of_containers, features)


def start_nodes(args, nr_of_containers, features):
    container_names = []
    log = logging.getLogger(__name__)
    log.info(h1('Starting ConductR'))
    ports = collect_ports(args, features)
    conductr_args = flatten([feature.conductr_args() for feature in features])
    conductr_features = flatten([feature.conductr_feature_envs() for feature in features])
    feature_conductr_roles = flatten([feature.conductr_roles() for feature in features])
    for i in range(nr_of_containers):
        container_name = '{prefix}{nr}'.format(prefix=CONDUCTR_NAME_PREFIX, nr=i)
        container_names.append(container_name)
        # Display the ports on the command line. Only if the user specifies a certain feature, then
        # the corresponding port will be displayed when running 'sandbox run' or 'sandbox debug'
        if ports:
            host_ip = host.DOCKER_IP
            ports_desc = ' exposing ' + ', '.join(['{}:{}'.format(host_ip, map_port(i, port))
                                                   for port in sorted(ports)])
        else:
            ports_desc = ''
        log.info('Starting container {container}{port_desc}..'.format(container=container_name,
                                                                      port_desc=ports_desc))
        cond0_ip = inspect_cond0_ip() if i > 0 else None
        conductr_container_roles = sandbox_common.resolve_conductr_roles_by_instance(args.conductr_roles,
                                                                                     feature_conductr_roles, i)
        run_conductr_cmd(
            i,
            nr_of_containers,
            container_name,
            cond0_ip,
            args.envs,
            '{image}:{version}'.format(image=args.image, version=args.image_version),
            args.log_level,
            ports,
            args.bundle_http_port,
            conductr_features,
            conductr_container_roles,
            conductr_args
        )
    return container_names


def collect_ports(args, features):
    """Return a Set of ports based on the ports of each enabled feature and the ports specified by the user"""

    feature_ports = flatten([feature.ports for feature in features])
    return set(args.ports + feature_ports)


def map_port(instance, port):
    current_port_str_rev = ''.join(reversed(str(port)))
    current_second_last_nr = int(current_port_str_rev[1])
    new_second_last_nr = current_second_last_nr if instance == 0 else (current_second_last_nr + instance) % 10
    new_port_str_rev = current_port_str_rev[0] + str(new_second_last_nr) + current_port_str_rev[2:]
    return ''.join(reversed(new_port_str_rev))


def inspect_cond0_ip():
    return terminal.docker_inspect('{}0'.format(CONDUCTR_NAME_PREFIX), '{{.NetworkSettings.IPAddress}}')


def run_conductr_cmd(instance, nr_of_instances, container_name, cond0_ip, envs, image, log_level, ports,
                     bundle_http_port, conductr_features, conductr_roles, conductr_args):
    general_args = ['-d', '--name', container_name]
    env_args = resolve_docker_run_envs(instance, nr_of_instances, envs, log_level, cond0_ip,
                                       conductr_features, conductr_roles, conductr_args)
    all_conductr_ports = CONDUCTR_PORTS | {bundle_http_port}
    port_args = resolve_docker_run_port_args(ports | all_conductr_ports, instance)
    optional_args = general_args + env_args + port_args
    additional_optional_args = resolve_conductr_docker_run_opts()
    positional_args = resolve_docker_run_positional_args(cond0_ip)
    terminal.docker_run(optional_args + additional_optional_args, image, positional_args)


def resolve_docker_run_envs(instance, nr_of_instances, envs, log_level, cond0_ip,
                            feature_names, conductr_roles, conductr_args):
    instance_env = ['CONDUCTR_INSTANCE={}'.format(instance), 'CONDUCTR_NR_OF_INSTANCES={}'.format(nr_of_instances)]
    log_level_env = ['AKKA_LOGLEVEL={}'.format(log_level)]
    syslog_ip_env = ['SYSLOG_IP={}'.format(cond0_ip)] if cond0_ip else []
    conductr_features_env = ['CONDUCTR_FEATURES={}'.format(','.join(feature_names))] if feature_names else []
    conductr_roles_env = ['CONDUCTR_ROLES={}'.format(','.join(conductr_roles))] if conductr_roles else []
    conductr_args_env = ['CONDUCTR_ARGS={}'.format(' '.join(conductr_args))] if conductr_args else []
    all_envs = envs + instance_env + log_level_env + syslog_ip_env + conductr_features_env + conductr_roles_env + conductr_args_env
    env_args = []
    for env in all_envs:
        env_args.append('-e')
        env_args.append(env)
    return env_args


def resolve_docker_run_port_args(ports, instance):
    port_args = []
    for port in ports:
        port_args.append('-p')
        port_args.append('{external_port}:{internal_port}'.format(external_port=map_port(instance, port),
                                                                  internal_port=port))
    return port_args


def resolve_docker_run_positional_args(cond0_ip):
    seed_node_arg = ['--seed', '{}:{}'.format(cond0_ip, 9004)] if cond0_ip else []
    return ['--discover-host-ip'] + seed_node_arg


def resolve_conductr_docker_run_opts():
    conductr_docker_run_opts = os.getenv('CONDUCTR_DOCKER_RUN_OPTS')
    if conductr_docker_run_opts:
        return conductr_docker_run_opts.split(' ')
    else:
        return []
