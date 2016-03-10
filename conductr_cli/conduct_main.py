import argcomplete
import argparse
from conductr_cli import \
    conduct_info, conduct_load, conduct_run, conduct_services,\
    conduct_stop, conduct_unload, conduct_version, conduct_logs,\
    conduct_events, conduct_acls, host, logging_setup
from conductr_cli.constants import \
    DEFAULT_PORT, DEFAULT_API_VERSION, DEFAULT_CLI_SETTINGS_DIR,\
    DEFAULT_CUSTOM_SETTINGS_FILE, DEFAULT_CUSTOM_PLUGINS_DIR,\
    DEFAULT_BUNDLE_RESOLVE_CACHE_DIR, DEFAULT_WAIT_TIMEOUT
from pyhocon import ConfigFactory
import os
import sys


def add_ip_and_port(sub_parser):
    sub_parser.add_argument('-i', '--ip',
                            help='The optional ConductR IP, defaults to one of the value in this order:'
                                 '$CONDUCTR_IP or'
                                 'IP address of the docker VM or'
                                 '`127.0.0.1`',
                            default=None)  # Default is set in run() function
    sub_parser.add_argument('-p', '--port',
                            type=int,
                            help='The optional ConductR port, defaults to $CONDUCTR_PORT or `9005`',
                            default=DEFAULT_PORT)


def add_verbose(sub_parser):
    sub_parser.add_argument('-v', '--verbose',
                            help='Print JSON response to the command',
                            default=False,
                            dest='verbose',
                            action='store_true')


def add_long_ids(sub_parser):
    sub_parser.add_argument('--long-ids',
                            help='Print long Bundle IDs',
                            default=False,
                            dest='long_ids',
                            action='store_true')


def add_api_version(sub_parser):
    sub_parser.add_argument('--api-version',
                            help='Sets which ConductR api version to be used',
                            default=DEFAULT_API_VERSION,
                            dest='api_version',
                            choices=conduct_version.supported_api_versions())


def add_local_connection_flag(sub_parser):
    sub_parser.add_argument('--local-connection',
                            default=True,
                            dest='local_connection',
                            help=argparse.SUPPRESS)


def add_cli_settings_dir(sub_parser):
    sub_parser.add_argument('--settings-dir',
                            help='Directory where ConductR CLI settings are stored, defaults to {}'.format(
                                DEFAULT_CLI_SETTINGS_DIR),
                            default=DEFAULT_CLI_SETTINGS_DIR,
                            dest='cli_settings_dir')


def add_custom_settings_file(sub_parser):
    sub_parser.add_argument('--custom-settings-file',
                            help='Configuration where custom settings for ConductR CLI are stored in HOCON format,'
                            'defaults to {}'.format(DEFAULT_CUSTOM_SETTINGS_FILE),
                            default=DEFAULT_CUSTOM_SETTINGS_FILE,
                            dest='custom_settings_file')


def add_custom_plugins_dir(sub_parser):
    sub_parser.add_argument('--custom-plugins-dir',
                            help='Directory where custom plugins for ConductR CLI are stored, defaults to {}'.format(
                                DEFAULT_CUSTOM_PLUGINS_DIR),
                            default=DEFAULT_CUSTOM_PLUGINS_DIR,
                            dest='custom_plugins_dir')


def add_bundle_resolve_cache_dir(sub_parser):
    sub_parser.add_argument('--resolve-cache-dir',
                            help='Directory where resolved bundles are cached, defaults to {}'.format(
                                DEFAULT_BUNDLE_RESOLVE_CACHE_DIR),
                            default=DEFAULT_BUNDLE_RESOLVE_CACHE_DIR,
                            dest='resolve_cache_dir')


def add_quiet_flag(sub_parser):
    sub_parser.add_argument('-q',
                            help='Prints affected bundle id on screen if enabled',
                            default=False,
                            dest='quiet',
                            action='store_true')


def add_wait_timeout(sub_parser):
    sub_parser.add_argument('--wait-timeout',
                            help='Timeout in seconds waiting for bundle scale to be achieved in conduct run, '
                                 'or bundle to be stopped in conduct stop, defaults to {}'.format(DEFAULT_WAIT_TIMEOUT),
                            default=DEFAULT_WAIT_TIMEOUT,
                            dest='wait_timeout')


def add_no_wait(sub_parser):
    sub_parser.add_argument('--no-wait',
                            help='Disables waiting for bundle scale to be achieved in conduct run, or bundle to be '
                                 'stopped in conduct stop, defaults to',
                            default=False,
                            dest='no_wait',
                            action='store_true')


def add_default_arguments(sub_parser):
    add_ip_and_port(sub_parser)
    add_verbose(sub_parser)
    add_quiet_flag(sub_parser)
    add_long_ids(sub_parser)
    add_api_version(sub_parser)
    add_local_connection_flag(sub_parser)
    add_cli_settings_dir(sub_parser)
    add_custom_settings_file(sub_parser)
    add_custom_plugins_dir(sub_parser)


def build_parser():
    # Main argument parser
    parser = argparse.ArgumentParser('conduct')
    subparsers = parser.add_subparsers(title='commands',
                                       help='Use one of the following sub commands')

    # Sub-parser for `version` sub-command
    version_parser = subparsers.add_parser('version',
                                           help='print version')
    version_parser.set_defaults(func=conduct_version.version)

    # Sub-parser for `info` sub-command
    info_parser = subparsers.add_parser('info',
                                        help='print bundle information')
    add_default_arguments(info_parser)
    info_parser.set_defaults(func=conduct_info.info)

    # Sub-parser for `services` sub-command
    services_parser = subparsers.add_parser('services',
                                            help='print service information')
    add_default_arguments(services_parser)
    services_parser.set_defaults(func=conduct_services.services)

    # Sub-parser for `acls` sub-command
    acls_parser = subparsers.add_parser('acls',
                                        help='print request ACL information')
    acls_parser.add_argument('protocol_family',
                             choices=conduct_acls.SUPPORTED_PROTOCOL_FAMILIES,
                             help='The protocol family of the ACL to be displayed, either http or tcp')
    add_default_arguments(acls_parser)
    acls_parser.set_defaults(func=conduct_acls.acls)

    # Sub-parser for `load` sub-command
    load_parser = subparsers.add_parser('load',
                                        help='load a bundle')
    load_parser.add_argument('bundle',
                             help='The path to the bundle')
    load_parser.add_argument('configuration',
                             nargs='?',
                             default=None,
                             help='The optional configuration for the bundle')
    add_default_arguments(load_parser)
    add_bundle_resolve_cache_dir(load_parser)
    add_wait_timeout(load_parser)
    add_no_wait(load_parser)
    load_parser.set_defaults(func=conduct_load.load)

    # Sub-parser for `run` sub-command
    run_parser = subparsers.add_parser('run',
                                       help='run a bundle')
    run_parser.add_argument('--scale',
                            type=int,
                            default=1,
                            help='The optional number of executions, defaults to 1')
    run_parser.add_argument('--affinity',
                            default=None,
                            help='The optional ID of the bundle to run alongside with (v1.1 onwards)')
    run_parser.add_argument('bundle',
                            help='The ID of the bundle')
    add_default_arguments(run_parser)
    add_wait_timeout(run_parser)
    add_no_wait(run_parser)
    run_parser.set_defaults(func=conduct_run.run)

    # Sub-parser for `stop` sub-command
    stop_parser = subparsers.add_parser('stop',
                                        help='stop a bundle')
    stop_parser.add_argument('bundle',
                             help='The ID of the bundle')
    add_default_arguments(stop_parser)
    add_wait_timeout(stop_parser)
    add_no_wait(stop_parser)
    stop_parser.set_defaults(func=conduct_stop.stop)

    # Sub-parser for `unload` sub-command
    unload_parser = subparsers.add_parser('unload',
                                          help='unload a bundle')
    unload_parser.add_argument('bundle',
                               help='The ID of the bundle')
    add_default_arguments(unload_parser)
    add_wait_timeout(unload_parser)
    add_no_wait(unload_parser)
    unload_parser.set_defaults(func=conduct_unload.unload)

    # Sub-parser for `events` sub-command
    events_parser = subparsers.add_parser('events',
                                          help='show bundle events')
    add_default_arguments(events_parser)
    events_parser.add_argument('-n', '--lines',
                               type=int,
                               default=10,
                               help='The number of events to fetch, defaults to 10')
    events_parser.add_argument('--date',
                               action='store_true',
                               help='Display the date of the events')
    events_parser.add_argument('--utc',
                               action='store_true',
                               help='Convert the date/time of the events to UTC')
    events_parser.add_argument('bundle',
                               help='The ID or name of the bundle')
    events_parser.set_defaults(func=conduct_events.events)

    # Sub-parser for `logs` sub-command
    logs_parser = subparsers.add_parser('logs',
                                        help='show bundle logs')
    add_default_arguments(logs_parser)
    logs_parser.add_argument('-n', '--lines',
                             type=int,
                             default=10,
                             help='The number of logs to fetch, defaults to 10')
    logs_parser.add_argument('--date',
                             action='store_true',
                             help='Display the date of the log')
    logs_parser.add_argument('--utc',
                             action='store_true',
                             help='Convert the date/time of the log to UTC')
    logs_parser.add_argument('bundle',
                             help='The ID or name of the bundle')
    logs_parser.set_defaults(func=conduct_logs.logs)

    return parser


def get_cli_parameters(args):
    parameters = ['']
    if vars(args).get('ip'):
        parameters.append('--ip {}'.format(args.ip))
    if vars(args).get('port', int(DEFAULT_PORT)) != int(DEFAULT_PORT):
        parameters.append('--port {}'.format(args.port))
    if vars(args).get('api_version', DEFAULT_API_VERSION) != DEFAULT_API_VERSION:
        parameters.append('--api-version {}'.format(args.api_version))
    return ' '.join(parameters)


def get_custom_settings(args):
    custom_settings_file = vars(args).get('custom_settings_file')
    if custom_settings_file and os.path.exists(custom_settings_file):
        print('Loading custom settings {}'.format(custom_settings_file))
        return ConfigFactory.parse_file(custom_settings_file)
    else:
        return None


def run():
    # Parse arguments
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if not vars(args).get('func'):
        parser.print_help()
    else:
        # Add custom plugin dir to import path
        custom_plugins_dir = vars(args).get('custom_plugins_dir')
        if custom_plugins_dir:
            sys.path.append(custom_plugins_dir)

        # Resolve default ip if the --ip argument hasn't been specified
        if not vars(args).get('ip'):
            # Returns None if an error has occurred
            args.ip = host.resolve_default_ip()
            if not args.ip:
                return
        else:
            args.local_connection = False

        args.cli_parameters = get_cli_parameters(args)
        args.custom_settings = get_custom_settings(args)
        logging_setup.configure_logging(args)

        is_completed_without_error = args.func(args)
        if not is_completed_without_error:
            exit(1)
