import argcomplete
import argparse
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE
from conductr_cli import sandbox_run, sandbox_stop, sandbox_init, sandbox_common, logging_setup


def build_parser():
    # Main argument parser
    parser = argparse.ArgumentParser('sandbox')
    subparsers = parser.add_subparsers(title='commands',
                                       help='Use one of the following sub commands')

    # Sub-parser for `run` sub-command
    run_parser = subparsers.add_parser('run',
                                       help='Run ConductR sandbox cluster',
                                       usage='%(prog)s IMAGE_VERSION [ARGS]',
                                       formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(run_parser)
    run_parser.add_argument('image_version',
                            nargs='?',
                            help='Version of the ConductR docker image to use.\n'
                                 'To obtain the current version and additional information, please visit the \n'
                                 'http://www.typesafe.com/product/conductr/developer page on Typesafe.com.')
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
                            type=int,
                            default=1,
                            help='Number of ConductR nodes. Defaults to 1.',
                            metavar='')
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
    features = ['visualization', 'logging', 'monitoring']
    run_parser.add_argument('-f', '--feature',
                            dest='features',
                            action='append',
                            default=[],
                            help='Features to be enabled.\n'
                                 'Available features: ' + ', '.join(features),
                            choices=features,
                            metavar='')
    run_parser.add_argument('--no-wait',
                            help='Disables waiting for ConductR to be started in the sandbox',
                            default=False,
                            dest='no_wait',
                            action='store_true')
    run_parser.set_defaults(func=sandbox_run.run)

    # Sub-parser for `debug` sub-command
    debug_parser = subparsers.add_parser('debug',
                                         help='Not supported. Use \'sbt-conductr-sandbox\' instead.')
    add_resolve_ip(debug_parser, False)
    debug_parser.set_defaults(func='debug')

    # Sub-parser for `stop` sub-command
    stop_parser = subparsers.add_parser('stop',
                                        help='Stop ConductR sandbox cluster')
    add_default_arguments(stop_parser)
    stop_parser.set_defaults(func=sandbox_stop.stop)

    # Sub-parser for `init` sub-command
    init_parser = subparsers.add_parser('init',
                                        help='Initializes ConductR sandbox environment')
    add_resolve_ip(init_parser, False)
    init_parser.set_defaults(func=sandbox_init.init)
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


def run():
    # Parse arguments
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    # Print help or execute subparser function
    if vars(args).get('func') is None:
        parser.print_help()
    # Exit with sandbox debug error message
    elif vars(args).get('func') == 'debug':
        parser.exit('Debugging a ConductR cluster is not supported by the \'conductr-cli\'.\n'
                    'Use the sbt plugin \'sbt-conductr-sandbox\' instead.')
    # Validate host IP address
    elif args.resolve_ip and not sandbox_common.resolve_host_ip():
        return
    # Validate image_version
    elif vars(args).get('func').__name__ == 'run' and not args.image_version:
        parser.exit('The version of the ConductR Docker image must be set.\n'
                    'Please visit https://www.typesafe.com/product/conductr/developer '
                    'to obtain the current version information.')
    # Call sandbox function
    else:
        logging_setup.configure_logging(args)
        args.func(args)
