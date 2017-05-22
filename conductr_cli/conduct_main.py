import argcomplete
import argparse
from conductr_cli import \
    bndl_main, conduct_agents, conduct_deploy, conduct_info, conduct_load, conduct_members, conduct_run, \
    conduct_service_names, conduct_stop, conduct_unload, version, conduct_logs, conduct_events, conduct_acls, \
    conduct_dcos, conduct_load_license, host, logging_setup, conduct_url, custom_settings
from conductr_cli.constants import \
    DEFAULT_SCHEME, DEFAULT_PORT, DEFAULT_BASE_PATH, \
    DEFAULT_API_VERSION, DEFAULT_DCOS_SERVICE, DEFAULT_CLI_SETTINGS_DIR, \
    DEFAULT_CUSTOM_SETTINGS_FILE, DEFAULT_CUSTOM_PLUGINS_DIR, DEFAULT_BUNDLE_RESOLVE_CACHE_DIR, \
    DEFAULT_CONFIGURATION_RESOLVE_CACHE_DIR, DEFAULT_WAIT_TIMEOUT, DEFAULT_OFFLINE_MODE, DEFAULT_LICENSE_DOWNLOAD_URL
from dcos import config, constants

from pathlib import Path
from urllib.parse import urlparse
import logging
import os
import sys


def add_scheme_host_ip_port_and_base_path(sub_parser):
    sub_parser.add_argument('--scheme',
                            help='The optional ConductR scheme, defaults to http',
                            default=DEFAULT_SCHEME)
    sub_parser.add_argument('--host',
                            help='The optional ConductR host\n'
                                 'Defaults to one of the value in this order:\n'
                                 '1. $CONDUCTR_HOST\n'
                                 '2. $CONDUCTR_IP\n'
                                 '3. IP address of the docker VM or\n'
                                 '4. 127.0.0.1',
                            default=None)  # Default is determined given the Docker environment
    sub_parser.add_argument('-i', '--ip',
                            help='The optional ConductR IP\n'
                                 'Defaults to one of the value in this order:\n'
                                 '1. $CONDUCTR_IP\n'
                                 '2. IP address of the docker VM\n'
                                 '3. 127.0.0.1',
                            default=None)  # Default is determined given the Docker environment
    sub_parser.add_argument('-p', '--port',
                            type=int,
                            help='The optional ConductR port\n'
                                 'Defaults to $CONDUCTR_PORT or 9005',
                            default=DEFAULT_PORT)
    sub_parser.add_argument('--base-path',
                            help='The optional ConductR base path\n'
                                 'Defaults to $DEFAULT_BASE_PATH or /',
                            default=DEFAULT_BASE_PATH)


def add_dcos_settings(sub_parser):
    sub_parser.add_argument('--service',
                            help='The ConductR service ID or name to direct requests to\n'
                                 'Defaults to conductr',
                            default=DEFAULT_DCOS_SERVICE)


def add_verbose(sub_parser):
    sub_parser.add_argument('-v', '--verbose',
                            help='Print detailed information of the command',
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
                            help='Sets which ConductR api version to be used\n'
                                 'Defaults to {}'.format(DEFAULT_API_VERSION),
                            default=DEFAULT_API_VERSION,
                            dest='api_version',
                            choices=version.supported_api_versions())


def add_local_connection_flag(sub_parser):
    sub_parser.add_argument('--local-connection',
                            default=True,
                            dest='local_connection',
                            help=argparse.SUPPRESS)


def add_cli_settings_dir(sub_parser):
    sub_parser.add_argument('--settings-dir',
                            help='Directory where ConductR CLI settings are stored\n'
                                 'Defaults to {}'.format(DEFAULT_CLI_SETTINGS_DIR),
                            default=DEFAULT_CLI_SETTINGS_DIR,
                            dest='cli_settings_dir')


def add_custom_settings_file(sub_parser):
    sub_parser.add_argument('--custom-settings-file',
                            help='Configuration where custom settings for ConductR CLI are stored in HOCON format\n'
                                 'Defaults to {}'.format(DEFAULT_CUSTOM_SETTINGS_FILE),
                            default=DEFAULT_CUSTOM_SETTINGS_FILE,
                            dest='custom_settings_file')


def add_custom_plugins_dir(sub_parser):
    sub_parser.add_argument('--custom-plugins-dir',
                            help='Directory where custom plugins for ConductR CLI are stored\n'
                                 'Defaults to {}'.format(DEFAULT_CUSTOM_PLUGINS_DIR),
                            default=DEFAULT_CUSTOM_PLUGINS_DIR,
                            dest='custom_plugins_dir')


def add_bundle_resolve_cache_dir(sub_parser):
    sub_parser.add_argument('--bundle-resolve-cache-dir',
                            help='Directory where resolved bundles are cached\n'
                                 'Defaults to {}'.format(DEFAULT_BUNDLE_RESOLVE_CACHE_DIR),
                            default=DEFAULT_BUNDLE_RESOLVE_CACHE_DIR,
                            dest='bundle_resolve_cache_dir')


def add_configuration_resolve_cache_dir(sub_parser):
    sub_parser.add_argument('--configuration-resolve-cache-dir',
                            help='Directory where resolved bundle configurations are cached\n'
                                 'Defaults to {}'.format(DEFAULT_CONFIGURATION_RESOLVE_CACHE_DIR),
                            default=DEFAULT_CONFIGURATION_RESOLVE_CACHE_DIR,
                            dest='configuration_resolve_cache_dir')


def add_disable_instructions(sub_parser):
    sub_parser.add_argument('--disable-instructions',
                            help='Disables further instruction output after the command has been succeeded\n'
                                 'Defaults to False',
                            default=False,
                            dest='disable_instructions',
                            action='store_true')


def add_quiet_flag(sub_parser):
    sub_parser.add_argument('-q',
                            help='Prints affected bundle id on screen if enabled\n'
                                 'Defaults to False',
                            default=False,
                            dest='quiet',
                            action='store_true')


def add_wait_timeout(sub_parser, wait_timeout=DEFAULT_WAIT_TIMEOUT):
    sub_parser.add_argument('--wait-timeout',
                            help='Timeout in seconds waiting for bundle scale to be achieved in conduct run\n'
                                 'or bundle to be stopped in conduct stop\n'
                                 'Defaults to {}'.format(wait_timeout),
                            type=int,
                            default=wait_timeout,
                            dest='wait_timeout')


def add_no_wait(sub_parser):
    sub_parser.add_argument('--no-wait',
                            help='Disables waiting for bundle scale to be achieved in conduct run\n'
                                 'or bundle to be stopped in conduct stop\n'
                                 'Defaults to False',
                            default=False,
                            dest='no_wait',
                            action='store_true')


def add_dcos_mode_args(sub_parser, dcos_mode):
    if not dcos_mode:
        add_scheme_host_ip_port_and_base_path(sub_parser)
    else:
        add_dcos_settings(sub_parser)


def add_date_args(sub_parser, show_help=True):
    sub_parser.add_argument('--utc',
                            action='store_true',
                            help='Convert the date/time of the events to UTC' if show_help else argparse.SUPPRESS)


def add_lines_args(subparser, show_help=True):
    subparser.add_argument('-n', '--lines',
                           type=int,
                           default=10,
                           help='The number of logs to fetch\n'
                                'Defaults to 10' if show_help else argparse.SUPPRESS)


def add_follow_args(subparser, show_help=True):
    subparser.add_argument('-f', '--follow',
                           help='Outputs log events as they occur. Analogous to UNIX\'s `tail -F`' if show_help
                           else argparse.SUPPRESS,
                           default=False,
                           dest='follow',
                           action='store_true')


def add_offline_mode(sub_parser):
    sub_parser.add_argument('--offline',
                            default=DEFAULT_OFFLINE_MODE,
                            dest='offline_mode',
                            action='store_true',
                            help='Enables offline mode to resolve bundles only locally\n'
                                 'either by file uri or from the cache directory\n'
                                 'True if CONDUCTR_OFFLINE_MODE environment variable is set\n'
                                 'False if --offline flag not specified and environment variable not set')


def add_default_arguments(sub_parser, dcos_mode):
    add_dcos_mode_args(sub_parser, dcos_mode)
    add_verbose(sub_parser)
    add_disable_instructions(sub_parser)
    add_quiet_flag(sub_parser)
    add_long_ids(sub_parser)
    add_api_version(sub_parser)
    add_local_connection_flag(sub_parser)
    add_cli_settings_dir(sub_parser)
    add_custom_settings_file(sub_parser)
    add_custom_plugins_dir(sub_parser)


def build_parser(dcos_mode):
    # Main argument parser
    parser = argparse.ArgumentParser('conduct', formatter_class=argparse.RawTextHelpFormatter)
    if dcos_mode:
        parser.add_argument('--info',
                            action='store_true',
                            dest='dcos_info')

    subparsers = parser.add_subparsers(title='commands',
                                       help='Use one of the following sub commands:')

    # Sub-parser for `version` sub-command
    version_parser = subparsers.add_parser('version',
                                           help='Print version',
                                           formatter_class=argparse.RawTextHelpFormatter)
    version_parser.set_defaults(func=version.version)

    # Sub-parser for `info` sub-command
    info_parser = subparsers.add_parser('info',
                                        help='Print bundle information',
                                        formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(info_parser, dcos_mode)
    info_parser.add_argument('bundle',
                             nargs='?',
                             default=None,
                             help='The optional id or name to the bundle.\n'
                                  'When specified detailed information pertaining to the bundle is displayed')
    info_parser.set_defaults(func=conduct_info.info)

    # Sub-parser for `service-names` sub-command
    service_names_parser = subparsers.add_parser('service-names',
                                                 help='Print the service names available to the service locator',
                                                 formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(service_names_parser, dcos_mode)
    service_names_parser.set_defaults(func=conduct_service_names.service_names)

    # Sub-parser for `acls` sub-command
    acls_parser = subparsers.add_parser('acls',
                                        help='Print request ACL information',
                                        formatter_class=argparse.RawTextHelpFormatter)
    acls_parser.add_argument('protocol_family',
                             choices=conduct_acls.SUPPORTED_PROTOCOL_FAMILIES,
                             help='The protocol family of the ACL to be displayed\n'
                                  'Either http or tcp')
    add_default_arguments(acls_parser, dcos_mode)
    acls_parser.set_defaults(func=conduct_acls.acls)

    # Sub-parser for `load` sub-command
    load_parser = subparsers.add_parser('load',
                                        help='Load a bundle',
                                        formatter_class=argparse.RawTextHelpFormatter)

    load_parser.add_argument('bundle',
                             nargs=None if sys.stdin.isatty() else '?',
                             default=None if sys.stdin.isatty() else '-',
                             help='The path to the bundle. Specify "-" to skip when providing stdin')

    load_parser.add_argument('configuration',
                             nargs='?',
                             default=None,
                             help='The optional configuration for the bundle')
    add_offline_mode(load_parser)
    add_default_arguments(load_parser, dcos_mode)
    add_bundle_resolve_cache_dir(load_parser)
    add_configuration_resolve_cache_dir(load_parser)
    add_wait_timeout(load_parser)
    add_no_wait(load_parser)
    bndl_main.add_conf_arguments(load_parser)
    load_parser.set_defaults(func=conduct_load.load)

    # Sub-parser for `run` sub-command
    run_parser = subparsers.add_parser('run',
                                       aliases=['start'],
                                       help='Run a bundle',
                                       formatter_class=argparse.RawTextHelpFormatter)
    run_parser.add_argument('--scale',
                            type=int,
                            default=1,
                            help='The optional number of executions\n'
                                 'Defaults to 1')
    run_parser.add_argument('--affinity',
                            default=None,
                            help='The optional ID of the bundle to run alongside with (v2.0 onwards)')
    run_parser.add_argument('bundle',
                            help='The ID of the bundle')
    add_default_arguments(run_parser, dcos_mode)
    add_wait_timeout(run_parser)
    add_no_wait(run_parser)

    # These are the arguments to display the bundle events and logs when error occurs during waiting for bundle scale.
    # As such, the help text for these arguments are not displayed.
    add_date_args(run_parser, show_help=False)
    add_lines_args(run_parser, show_help=False)
    add_follow_args(run_parser, show_help=False)

    run_parser.set_defaults(func=conduct_run.run)

    # Sub-parser for `stop` sub-command
    stop_parser = subparsers.add_parser('stop',
                                        help='Stop a bundle',
                                        formatter_class=argparse.RawTextHelpFormatter)
    stop_parser.add_argument('bundle',
                             help='The ID of the bundle')
    add_default_arguments(stop_parser, dcos_mode)
    add_wait_timeout(stop_parser)
    add_no_wait(stop_parser)

    # These are the arguments to display the bundle events and logs when error occurs during waiting for bundle scale.
    # As such, the help text for these arguments are not displayed.
    add_date_args(stop_parser, show_help=False)
    add_lines_args(stop_parser, show_help=False)
    add_follow_args(stop_parser, show_help=False)

    stop_parser.set_defaults(func=conduct_stop.stop)

    # Sub-parser for `unload` sub-command
    unload_parser = subparsers.add_parser('unload',
                                          help='Unload a bundle',
                                          formatter_class=argparse.RawTextHelpFormatter)
    unload_parser.add_argument('bundle',
                               help='The ID of the bundle')
    add_default_arguments(unload_parser, dcos_mode)
    add_wait_timeout(unload_parser)
    add_no_wait(unload_parser)
    unload_parser.set_defaults(func=conduct_unload.unload)

    # Sub-parser for `events` sub-command
    events_parser = subparsers.add_parser('events',
                                          help='Show bundle events',
                                          formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(events_parser, dcos_mode)
    add_lines_args(events_parser)
    add_date_args(events_parser)
    events_parser.add_argument('bundle',
                               help='The ID or name of the bundle')
    events_parser.set_defaults(func=conduct_events.events)

    # Sub-parser for `logs` sub-command
    logs_parser = subparsers.add_parser('logs',
                                        help='Show bundle logs',
                                        formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(logs_parser, dcos_mode)
    add_lines_args(logs_parser)
    add_follow_args(logs_parser)
    add_date_args(logs_parser)
    logs_parser.add_argument('bundle',
                             help='The ID or name of the bundle')
    logs_parser.set_defaults(func=conduct_logs.logs)

    # Sub-parser for `setup-dcos` sub-command
    dcos_parser = subparsers.add_parser('setup-dcos',
                                        help='Setup integration with the DC/OS CLI\n'
                                             'so that \'dcos conduct ..\' commands can\n'
                                             'be used to access ConductR via DC/OS',
                                        formatter_class=argparse.RawTextHelpFormatter)
    dcos_parser.set_defaults(func=conduct_dcos.setup)

    # Sub-parser for `deploy` sub-command
    deploy_parser = subparsers.add_parser('deploy',
                                          help='Replaces a running bundle with a deployed version',
                                          formatter_class=argparse.RawTextHelpFormatter)
    deploy_parser.add_argument('bundle',
                               nargs=None if sys.stdin.isatty() else '?',
                               default=None if sys.stdin.isatty() else '-',
                               help='The path to the bundle. Specify "-" to skip when providing stdin')
    deploy_parser.add_argument('configuration',
                               nargs='?',
                               default=None,
                               help='The optional configuration for the bundle')
    deploy_parser.add_argument('-y',
                               action='store_true',
                               default=False,
                               dest='auto_deploy',
                               help='If supplied, deployment will proceed without prompt')
    deploy_parser.add_argument('--target-tag',
                               action='append',
                               default=[],
                               dest='target_tags',
                               help='If supplied, deployment will be performed on the bundles with matching tag.\n'
                                    'If multiple tags are supplied, deployment will be performed for each supplied tag.')
    deploy_parser.add_argument('--webhook',
                               default=None,
                               dest='webhook',
                               help='If supplied, the command will simulate the provided webhook.\n'
                                    'Currently supports `bintray`.')
    add_dcos_mode_args(deploy_parser, dcos_mode)
    add_api_version(deploy_parser)
    add_local_connection_flag(deploy_parser)
    add_cli_settings_dir(deploy_parser)
    add_custom_settings_file(deploy_parser)
    add_custom_plugins_dir(deploy_parser)
    add_offline_mode(deploy_parser)
    add_bundle_resolve_cache_dir(deploy_parser)
    add_configuration_resolve_cache_dir(deploy_parser)
    add_wait_timeout(deploy_parser, wait_timeout=conduct_deploy.DEFAULT_WAIT_TIMEOUT)
    add_no_wait(deploy_parser)
    bndl_main.add_conf_arguments(deploy_parser)
    add_long_ids(deploy_parser)
    deploy_parser.set_defaults(func=conduct_deploy.deploy)

    # Sub-parser for `members` sub-command
    members_parser = subparsers.add_parser('members',
                                           help='Display cluster member information',
                                           formatter_class=argparse.RawTextHelpFormatter)

    add_default_arguments(members_parser, dcos_mode)

    members_parser.add_argument('--role',
                                help='Show only agents with supplied role',
                                default=None)

    members_parser.set_defaults(func=conduct_members.members)

    # Sub-parser for `agents` sub-command
    agents_parser = subparsers.add_parser('agents',
                                          help='Display agent information',
                                          formatter_class=argparse.RawTextHelpFormatter)

    add_default_arguments(agents_parser, dcos_mode)

    agents_parser.add_argument('--role',
                               help='Show only agents with supplied role',
                               default=None)

    agents_parser.set_defaults(func=conduct_agents.agents)

    # Sub-parser for `load-license` sub-command
    load_license_parser = subparsers.add_parser('load-license',
                                                help='Obtains license from Lightbend.com and '
                                                     'loads the license into ConductR',
                                                formatter_class=argparse.RawTextHelpFormatter)

    add_dcos_mode_args(load_license_parser, dcos_mode)
    add_api_version(load_license_parser)
    add_local_connection_flag(load_license_parser)
    add_offline_mode(load_license_parser)
    add_cli_settings_dir(load_license_parser)
    add_custom_settings_file(load_license_parser)
    add_custom_plugins_dir(load_license_parser)
    add_quiet_flag(load_license_parser)
    add_verbose(load_license_parser)
    load_license_parser.add_argument('-f', '--force',
                                     dest='force_flag_enabled',
                                     default=False,
                                     action='store_true',
                                     help='Always prompts for authentication token when specified,\n'
                                          'use this option to change authentication token between different users')
    load_license_parser.add_argument('--license-download-url',
                                     dest='license_download_url',
                                     help=argparse.SUPPRESS,
                                     default=DEFAULT_LICENSE_DOWNLOAD_URL)

    load_license_parser.set_defaults(func=conduct_load_license.load_license)

    return parser


def get_cli_parameters(args):
    parameters = ['']
    arg = vars(args).get('scheme')
    if not args.dcos_mode and arg and arg != DEFAULT_SCHEME:
        parameters.append('--scheme {}'.format(args.scheme))
    arg = vars(args).get('host')
    if not args.dcos_mode and arg and arg != host.resolve_default_host():
        parameters.append('--host {}'.format(args.host))
    arg = vars(args).get('ip')
    if not args.dcos_mode and arg and arg != host.resolve_default_ip():
        parameters.append('--ip {}'.format(args.ip))
    arg = vars(args).get('port', int(DEFAULT_PORT))
    if not args.dcos_mode and arg and arg != int(DEFAULT_PORT):
        parameters.append('--port {}'.format(args.port))
    arg = vars(args).get('base_path', DEFAULT_BASE_PATH)
    if not args.dcos_mode and arg and arg != DEFAULT_BASE_PATH:
        parameters.append('--base-path {}'.format(args.base_path))
    arg = vars(args).get('api_version', DEFAULT_API_VERSION)
    if arg and arg != DEFAULT_API_VERSION:
        parameters.append('--api-version {}'.format(args.api_version))
    return ' '.join(parameters)


def disable_urllib3_warnings():
    from requests.packages import urllib3
    from requests.packages.urllib3 import exceptions
    # Disable urllib3 warning since it's going to break `conduct load` with `-q` flag specified.
    # The reason of disabling the warning will be explained below.

    # The warning will be raised if the Subject Alt Naming field is not present in the SSL cert.
    # Subject Alt Naming field is replacement for the Common Name which is deprecated according to RFC 2818:
    # https://tools.ietf.org/html/rfc2818
    #
    # However it seems the deprecation of the Common Name has been a slow progress. For example, OpenSSL 0.9.8 released
    # in July 2015 does not allow generating Subject Alt Naming field out of the box, instead the user is expected to
    # modify the machine's openssl.cnf in order to append this field into the generated cert.
    #
    # This warning is introduced from to https://github.com/shazow/urllib3/issues/497
    urllib3.disable_warnings(exceptions.SubjectAltNameWarning)


def run(_args=[], configure_logging=True):
    # If we're being invoked via DC/OS then route our http
    # calls via its extension to the requests library. In
    # addition remove the 'conduct-dcos' and 'conduct' arg so that the conduct
    # sub-commands are positioned correctly, along with their
    # arguments.
    if sys.argv and Path(sys.argv[0]).name == constants.DCOS_COMMAND_PREFIX + 'conduct':
        dcos_mode = True
        _args = sys.argv[2:]
    else:
        dcos_mode = False
        if not _args:
            # Remove the 'conduct' arg so that we start with the sub command directly
            _args = sys.argv[1:]
    # Parse arguments
    parser = build_parser(dcos_mode)
    argcomplete.autocomplete(parser)
    args = parser.parse_args(_args)
    args.dcos_mode = dcos_mode
    if not vars(args).get('func'):
        if vars(args).get('dcos_info'):
            print('Lightbend ConductR sub commands. Type \'dcos conduct\' to see more.')
            sys.exit(0)
        else:
            parser.print_help()
    else:
        # Offline functions are the functions which do not require network to run, e.g. `conduct version` or
        # `conduct setup-dcos`.
        offline_functions = ['version', 'setup']

        # Only setup network related args (i.e. host, bundle resolvers, basic auth, etc) for functions which requires
        # connectivity to ConductR.
        current_function = vars(args).get('func').__name__
        if current_function not in offline_functions:
            # Add custom plugin dir to import path
            custom_plugins_dir = vars(args).get('custom_plugins_dir')
            if custom_plugins_dir:
                sys.path.append(custom_plugins_dir)

            # DC/OS provides the location of ConductR...
            if dcos_mode:
                args.command = 'dcos conduct'
                dcos_url = urlparse(config.get_config_val('core.dcos_url'))
                args.scheme = dcos_url.scheme
                args.ip = dcos_url.hostname
                default_http_port = 80 if dcos_url.scheme == 'http' else 443
                args.port = dcos_url.port if dcos_url.port else default_http_port
                dcos_url_path = dcos_url.path if dcos_url.path else '/'
                args.base_path = dcos_url_path + 'service/{}/'.format(DEFAULT_DCOS_SERVICE)
            else:
                args.command = 'conduct'

            # Set ConductR host is --host or --ip argument not set
            # Also set the local_connection argument accordingly
            host_from_args = conduct_url.conductr_host(args)
            if not host_from_args:
                host_from_env = host.resolve_host_from_env()
                if host_from_env:
                    args.host = host_from_env
                    args.local_connection = False
                else:
                    args.host = host.resolve_default_host()
            else:
                args.local_connection = False

            args.cli_parameters = get_cli_parameters(args)
            args.custom_settings = custom_settings.load_from_file(args)

            args.conductr_auth = custom_settings.load_conductr_credentials(args)

            # Ensure HTTPS is used if authentication is configured
            if args.conductr_auth and args.scheme != 'https':
                args.scheme = 'https'

            args.server_verification_file = custom_settings.load_server_ssl_verification_file(args)
            # Ensure verification file exists if specified
            if args.server_verification_file \
                    and not os.path.exists(args.server_verification_file):
                # Configure logging so error message can be logged properly before exiting with failure
                logging_setup.configure_logging(args)
                log = logging.getLogger(__name__)
                log.error('Ensure server SSL verification file exists: {}'.format(args.server_verification_file))
                sys.exit(1)

            if not args.dcos_mode and args.scheme == 'https':
                disable_urllib3_warnings()

        if configure_logging:
            logging_setup.configure_logging(args)

        is_completed_without_error = args.func(args)
        if not is_completed_without_error:
            sys.exit(1)
