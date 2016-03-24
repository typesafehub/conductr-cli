from conductr_cli import sandbox_common, terminal, validation
from conductr_cli.sandbox_common import CONDUCTR_NAME_PREFIX, CONDUCTR_DEV_IMAGE, CONDUCTR_PORTS
import logging


@validation.handle_docker_errors
def run(args):
    """`sandbox run` command"""

    pull_image(args)
    ports = collect_ports(args)
    scale_cluster(args, ports)


def pull_image(args):
    if args.image == CONDUCTR_DEV_IMAGE and not terminal.docker_images(CONDUCTR_DEV_IMAGE):
        log = logging.getLogger(__name__)
        log.info('Pulling down the ConductR development image..')
        terminal.docker_pull('{image_name}:{image_version}'
                             .format(image_name=CONDUCTR_DEV_IMAGE, image_version=args.image_version))


def collect_ports(args):
    """Return a Set of ports based on the ports of each enabled feature and the ports specified by the user"""

    def to_feature(feature_name):
        if feature_name == 'visualization':
            return {'name': feature_name, 'ports': [9999]}
        elif feature_name == 'logging':
            return {'name': feature_name, 'ports': [5601]}
        elif feature_name == 'monitoring':
            return {'name': feature_name, 'ports': []}

    all_feature_ports = [to_feature(feature_name)['ports'] for feature_name in args.features]
    return set(args.ports + [port for feature_ports in all_feature_ports for port in feature_ports])


def scale_cluster(args, ports):
    running_containers = sandbox_common.resolve_running_docker_containers()
    if args.nr_of_containers > len(running_containers):
        start_nodes(args, ports)
    elif args.nr_of_containers < len(running_containers):
        stop_nodes(args, running_containers)
    else:
        log = logging.getLogger(__name__)
        log.info('ConductR nodes {} already exists, leaving them alone.'.format(', '.join(running_containers)))


def start_nodes(args, ports):
    log = logging.getLogger(__name__)

    log.info('Starting ConductR nodes..')
    for i in range(args.nr_of_containers):
        container_name = '{prefix}{nr}'.format(prefix=CONDUCTR_NAME_PREFIX, nr=i)
        container_id = terminal.docker_ps('name={}'.format(container_name))
        if not container_id:
            # Display the ports on the command line. Only if the user specifies a certain feature, then
            # the corresponding port will be displayed when running 'sandbox run' or 'sandbox debug'
            if ports:
                host_ip = sandbox_common.resolve_host_ip()
                ports_desc = ' exposing ' + ', '.join(['{}:{}'.format(host_ip, map_port(i, port)) for port in sorted(ports)])
            else:
                ports_desc = ''
            log.info('Starting container {container}{port_desc}..'.format(container=container_name, port_desc=ports_desc))
            cond0_ip = inspect_cond0_ip() if i > 0 else None
            conductr_container_roles = resolve_conductr_roles_by_container(args.conductr_roles, i)
            run_conductr_cmd(
                i,
                container_name,
                cond0_ip,
                args.envs,
                '{image}:{version}'.format(image=args.image, version=args.image_version),
                args.log_level,
                ports,
                args.bundle_http_port,
                args.features,
                conductr_container_roles
            )
        else:
            log.info('ConductR node {} already exists, leaving it alone.'.format(container_name))


def map_port(instance, port):
    current_port_str_rev = ''.join(reversed(str(port)))
    current_second_last_nr = int(current_port_str_rev[1])
    new_second_last_nr = current_second_last_nr if instance == 0 else (current_second_last_nr + instance) % 10
    new_port_str_rev = current_port_str_rev[0] + str(new_second_last_nr) + current_port_str_rev[2:]
    return ''.join(reversed(new_port_str_rev))


def inspect_cond0_ip():
    return terminal.docker_inspect('{}0'.format(CONDUCTR_NAME_PREFIX), '{{.NetworkSettings.IPAddress}}')


def resolve_conductr_roles_by_container(conductr_roles, instance):
    if not conductr_roles:
        # No ConductR roles have been specified => Return an empty Set
        return set()
    elif instance + 1 <= len(conductr_roles):
        # Roles have been specified for the current ConductR instance => Get and use these roles.
        return conductr_roles[instance]
    else:
        # The current ConductR instance is greater than the length of conductr_roles.
        # In this case the roles of conductr_roles are subsequently applied to the remaining instances.
        remainder = (instance + 1) % len(conductr_roles)
        remaining_instance = len(conductr_roles) if remainder == 0 else remainder
        return conductr_roles[remaining_instance - 1]


def run_conductr_cmd(instance, container_name, cond0_ip, envs, image, log_level, ports, bundle_http_port, feature_names, conductr_roles):
    general_args = ['-d', '--name', container_name]
    env_args = resolve_docker_run_envs(envs, log_level, cond0_ip, feature_names, conductr_roles)
    all_conductr_ports = CONDUCTR_PORTS | {bundle_http_port}
    port_args = resolve_docker_run_port_args(ports | all_conductr_ports, instance)
    optional_args = general_args + env_args + port_args
    positional_args = resolve_docker_run_positional_args(cond0_ip)
    terminal.docker_run(optional_args, image, positional_args)


def resolve_docker_run_envs(envs, log_level, cond0_ip, feature_names, conductr_roles):
    log_level_env = ['AKKA_LOGLEVEL={}'.format(log_level)]
    syslog_ip_env = ['SYSLOG_IP={}'.format(cond0_ip)] if cond0_ip else []
    conductr_features_env = ['CONDUCTR_FEATURES={}'.format(','.join(feature_names))] if feature_names else []
    conductr_roles_env = ['CONDUCTR_ROLES={}'.format(','.join(conductr_roles))] if conductr_roles else []
    all_envs = envs + log_level_env + syslog_ip_env + conductr_features_env + conductr_roles_env
    env_args = []
    for env in all_envs:
        env_args.append('-e')
        env_args.append(env)
    return env_args


def resolve_docker_run_port_args(ports, instance):
    port_args = []
    for port in ports:
        port_args.append('-p')
        port_args.append('{external_port}:{internal_port}'.format(external_port=map_port(instance, port), internal_port=port))
    return port_args


def resolve_docker_run_positional_args(cond0_ip):
    seed_node_arg = ['--seed', '{}:{}'.format(cond0_ip, 9004)] if cond0_ip else []
    return ['--discover-host-ip'] + seed_node_arg


def stop_nodes(args, running_containers):
    log = logging.getLogger(__name__)

    log.info('Stopping ConductR nodes..')
    last_containers = len(running_containers) - args.nr_of_containers
    containers_to_be_stopped = running_containers[-last_containers:]
    return terminal.docker_rm(containers_to_be_stopped)
