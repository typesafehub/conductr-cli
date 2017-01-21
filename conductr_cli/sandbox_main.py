import argcomplete
import argparse
import ipaddress
import re
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE, major_version
from conductr_cli.sandbox_features import feature_names
from conductr_cli.constants import DEFAULT_SANDBOX_ADDR_RANGE, DEFAULT_SANDBOX_IMAGE_DIR, DEFAULT_OFFLINE_MODE
from conductr_cli import sandbox_run, sandbox_stop, sandbox_common, sandbox_ps, logging_setup, docker, version
from conductr_cli.sandbox_run_jvm import NR_OF_INSTANCE_EXPRESSION


def build_parser():
    # Main argument parser
    parser = argparse.ArgumentParser('sandbox')
    subparsers = parser.add_subparsers(title='commands',
                                       help='Use one of the following sub commands')

    # Sub-parser for `version` sub-command
    version_parser = subparsers.add_parser('version',
                                           help='print version')
    version_parser.set_defaults(func=version.version)

    # Sub-parser for `run` sub-command
    run_parser = subparsers.add_parser('run',
                                       help='Run ConductR sandbox cluster',
                                       usage='%(prog)s IMAGE_VERSION [ARGS]',
                                       formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(run_parser)
    add_image_dir(run_parser)
    run_parser.add_argument('image_version',
                            nargs='?',
                            help='Version of the ConductR docker image to use.\n'
                                 'To obtain the current version and additional information, please visit \n'
                                 'http://lightbend.com/product/conductr/developer')
    run_parser.add_argument('-r', '--conductr-role',
                            dest='conductr_roles',
                            action='append',
                            nargs='*',
                            default=[],
                            help='Set additional roles allowed per ConductR node.\n'
                                 'Multiple roles per node are separated by a whitespace.\n'
                                 'Example: sandbox run IMAGE_VERSION -r role1 role2 -r role3\n'
                                 'In this example the roles role1 and role2 are assigned to the first node and\n'
                                 'role3 is assigned to the second node.\n'
                                 'Afterwards the specified roles are subsequently applied to the remaining nodes.\n'
                                 'Defaults to [].',
                            metavar='')
    run_parser.add_argument('-e', '--env',
                            dest='envs',
                            action='append',
                            default=[],
                            help='Set additional environment variables for each ConductR container. Defaults to [].',
                            metavar='')
    run_parser.add_argument('-i', '--image',
                            default=CONDUCTR_DEV_IMAGE,
                            help='Docker image to use.\n'
                                 'Defaults to `{}`.'.format(CONDUCTR_DEV_IMAGE),
                            metavar='')
    log_levels = ['debug', 'info', 'warning']
    run_parser.add_argument('-l', '--log-level',
                            default='info',
                            help='Log level of ConductR.\n'
                                 'Defaults to `info`.\n'
                                 'You can observe ConductRs logging via the `docker logs` command. \n'
                                 'For example `docker logs -f cond-0` will follow the logs of the first '
                                 'ConductR container.\n'
                                 'Available log levels: ' + ', '.join(log_levels),
                            choices=log_levels,
                            metavar='')
    run_parser.add_argument('-n', '--nr-of-containers',
                            type=nr_of_containers,
                            default='1',
                            help='Number of ConductR core and agent instances. Defaults to 1.\n'
                                 'Also accepts `x:y` format: `x` is a number of core instances, '
                                 'and y is a number of agent instances\n'
                                 'For ConductR 1, this corresponds to the number of nodes.',
                            metavar='')
    run_parser.add_argument('--offline',
                            default=DEFAULT_OFFLINE_MODE,
                            dest='offline_mode',
                            action='store_true',
                            help='Enables offline mode to resolve bundles only locally '
                                 'either by file uri or from the cache directory. '
                                 'Defaults to environment variable CONDUCTR_OFFLINE_MODE. '
                                 'If not set the default is False.')
    run_parser.add_argument('-p', '--port',
                            dest='ports',
                            action='append',
                            type=int,
                            default=[],
                            help='Set additional ports to be made public by each of the ConductR containers.',
                            metavar='')
    run_parser.add_argument('--bundle-http-port',
                            dest='bundle_http_port',
                            type=int,
                            default=sandbox_common.bundle_http_port(),
                            help='Set default frontend port for proxying HTTP based request ACLs.',
                            metavar='')
    run_parser.add_argument('-f', '--feature',
                            dest='features',
                            action='append',
                            nargs='*',
                            default=[],
                            help='Features to be enabled.\n'
                                 'Available features: ' + ', '.join(feature_names),
                            metavar='')
    run_parser.add_argument('--no-wait',
                            help='Disables waiting for ConductR to be started in the sandbox.',
                            default=False,
                            dest='no_wait',
                            action='store_true')
    run_parser.add_argument('--addr-range',
                            type=addr_range,
                            default=DEFAULT_SANDBOX_ADDR_RANGE,
                            help='Range of address which will be used by ConductR Sandbox to bind to.\n'
                                 'The address range is specified using CIDR notation, i.e. 192.168.1.0/24')
    run_parser.set_defaults(func=sandbox_run.run)

    # Sub-parser for `stop` sub-command
    stop_parser = subparsers.add_parser('stop',
                                        help='Stop ConductR sandbox cluster')
    add_image_dir(stop_parser)
    add_default_arguments(stop_parser)
    stop_parser.set_defaults(func=sandbox_stop.stop)

    # Sub-parser for `ps` sub-command
    ps_parser = subparsers.add_parser('ps',
                                      help='List the pids for ConductR core and agent sandbox processes')
    add_image_dir(ps_parser)
    add_default_arguments(ps_parser)
    ps_parser.add_argument('--core',
                           help='Displays ConductR core sandbox process only.',
                           default=False,
                           dest='is_filter_core',
                           action='store_true')
    ps_parser.add_argument('--agent',
                           help='Displays ConductR agent sandbox process only.',
                           default=False,
                           dest='is_filter_agent',
                           action='store_true')
    ps_parser.add_argument('-q', '--quiet',
                           help='Displays only the pids without the column headers.',
                           default=False,
                           dest='is_quiet',
                           action='store_true')
    ps_parser.set_defaults(func=sandbox_ps.ps)

    return parser


def add_default_arguments(sub_parser):
    sub_parser.add_argument('--local-connection',
                            default=True,
                            help=argparse.SUPPRESS)
    add_resolve_ip(sub_parser, True)


def add_resolve_ip(sub_parser, default_value):
    sub_parser.add_argument('--resolve-ip',
                            default=default_value,
                            dest='resolve_ip',
                            action='store_true',
                            help=argparse.SUPPRESS)


def add_image_dir(sub_parser):
    sub_parser.add_argument('--image-dir',
                            default=DEFAULT_SANDBOX_IMAGE_DIR,
                            help='Default directory where sandbox images is stored.')


def run():
    # Parse arguments
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # Print help or execute subparser function
    if not vars(args).get('func'):
        parser.print_help()
    # Validate image_version
    elif vars(args).get('func').__name__ == 'run' and not args.image_version:
        parser.exit('The version of the ConductR Docker image must be set.\n'
                    'Please visit https://www.lightbend.com/product/conductr/developer '
                    'to obtain the current version information.')
    # Call sandbox function
    elif vars(args).get('func').__name__ == 'version':
        logging_setup.configure_logging(args)
        args.func(args)
    else:
        logging_setup.configure_logging(args)
        # Check that all feature arguments are valid
        if vars(args).get('func').__name__ == 'run':
            if args.features and args.no_wait:
                parser.exit('Option --no-wait is not allowed when starting ConductR with option --feature')
            invalid_features = [f for f, *a in args.features if f not in feature_names]
            if invalid_features:
                parser.exit('Invalid features: %s (choose from %s)' %
                            (', '.join("'%s'" % f for f in invalid_features),
                             ', '.join("'%s'" % f for f in feature_names)))
        # Docker VM validation
        args.vm_type = docker.vm_type()
        if vars(args).get('func').__name__ == 'run' and major_version(args.image_version) == 1:
            docker.validate_docker_vm(args.vm_type)

        result = args.func(args)
        if not result:
            exit(1)


def nr_of_containers(value):
    try:
        # Ensure value can be converted into an integer
        int(value)
        return value
    except ValueError:
        # Otherwise, ensure value follows the expected pattern
        match = re.search(NR_OF_INSTANCE_EXPRESSION, value)
        if match:
            return value
        else:
            raise argparse.ArgumentTypeError('Number of containers has to be an int, or <x>:<y> where '
                                             '`x` is an int corresponding to the number of core instances, and '
                                             '`y` is an int corresponding to the number of agent instances')


def addr_range(value):
    try:
        return ipaddress.ip_network(value, strict=True)
    except ValueError:
        raise argparse.ArgumentTypeError('{} is not a valid CIDR address range - '
                                         '`192.168.1.0/24` is an example of a valid CIDR address range'.format(value))
